from rest_framework import serializers
from .models import VolunteerOpportunity, VolunteerOpportunityApplication
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.urls import reverse

Account = get_user_model()

class VolunteerOpportunitySerializer(serializers.ModelSerializer):
    contribution_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = VolunteerOpportunity
        fields = '__all__'

    def validate(self, data):
        ongoing = data.get('ongoing', False)

        # Ensure required fields based on 'ongoing' status
        if ongoing:
            if 'days_of_week' not in data or not data['days_of_week']:
                raise serializers.ValidationError("Days of the week must be specified for ongoing opportunities.")
            if data.get('opportunity_date') is not None:
                raise serializers.ValidationError("Ongoing opportunities must not have an opportunity date.")
        else:
            if 'opportunity_date' not in data:
                raise serializers.ValidationError("Opportunity date is required for one-time opportunities.")
            if 'opportunity_time_from' not in data or 'opportunity_time_to' not in data:
                raise serializers.ValidationError("Time range (from and to) is required for one-time opportunities.")

        # Validate `requirements` (Must have at least 1 skill)
        if 'requirements' in data:
            if not isinstance(data['requirements'], list) or len(data['requirements']) == 0:
                raise serializers.ValidationError("At least one skill must be provided in the requirements.")

        # Ensure `area_of_work` is set and is **exactly** one choice
        if 'area_of_work' in data:
            valid_fields = [choice[0] for choice in VolunteerOpportunity.FIELDS_OF_INTEREST_CHOICES]
            if data['area_of_work'] not in valid_fields:
                raise serializers.ValidationError(f"Area of work must be one of {valid_fields}.")

        return data

    def create(self, validated_data):
        # Auto-set contribution_hours (Only if opportunity is one-time)
        if not validated_data.get('ongoing', False) and 'opportunity_time_from' in validated_data and 'opportunity_time_to' in validated_data:
            validated_data['contribution_hours'] = max(0, 
                (validated_data['opportunity_time_to'].hour + validated_data['opportunity_time_to'].minute / 60) -
                (validated_data['opportunity_time_from'].hour + validated_data['opportunity_time_from'].minute / 60)
            )

        return super().create(validated_data)
    
class VolunteerOpportunityApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerOpportunityApplication
        fields = '__all__'

    # Ensure an application meets all requirements before saving.
    def validate(self, data):
        opportunity = data['volunteer_opportunity']
        as_group = data.get('as_group', False)
        no_of_additional_volunteers = data.get('no_of_additional_volunteers', 0)

        # Check if opportunity has available slots (only for one-time opportunities)
        if not opportunity.ongoing and opportunity.slots < (1 + no_of_additional_volunteers):
            raise serializers.ValidationError("Not enough slots available for this opportunity.")

        # Ensure valid group application constraints
        if as_group and no_of_additional_volunteers < 1:
            raise serializers.ValidationError("Group applications must have at least one additional volunteer.")
        if not as_group and no_of_additional_volunteers != 0:
            raise serializers.ValidationError("Number of additional volunteers must be zero if applying alone.")

        return data

    # Override create method to handle additional logic
    def create(self, validated_data):
        return super().create(validated_data)

    # Deduct slots only when an application is accepted.
    def update(self, instance, validated_data):
        new_status = validated_data.get("application_status", instance.application_status)
        opportunity = instance.volunteer_opportunity

        # If application is changing from pending → accepted, deduct slots
        if new_status == "accepted" and instance.application_status != "accepted":
            if not opportunity.ongoing:
                total_slots_needed = 1 + instance.no_of_additional_volunteers
                if opportunity.slots < total_slots_needed:
                    raise serializers.ValidationError("Not enough slots available for this opportunity.")
                opportunity.slots -= total_slots_needed
                opportunity.save()

        # If application was already accepted, prevent modification
        if instance.application_status == "accepted" and new_status != "accepted":
            raise serializers.ValidationError("Cannot modify an already accepted application.")

        return super().update(instance, validated_data)