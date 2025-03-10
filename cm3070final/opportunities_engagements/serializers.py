from rest_framework import serializers
from .models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerEngagementLog, VolunteerEngagement, VolunteerOpportunitySession, VolunteerSessionEngagement
from volunteers_organizations.models import Organization
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from volunteers_organizations.serializers import OrganizationSerializer

Account = get_user_model()

class VolunteerOpportunitySerializer(serializers.ModelSerializer):
    contribution_hours = serializers.SerializerMethodField()  # Dynamically calculated, not stored
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = VolunteerOpportunity
        fields = '__all__'  # contribution_hours is read-only and computed

    # Dynamically calculate contribution hours from engagement logs.
    def get_contribution_hours(self, obj):
        logs = VolunteerEngagementLog.objects.filter(
            volunteer_engagement__volunteer_opportunity_application__volunteer_opportunity=obj,
            status="approved"  # Only count approved logs
        )
        return sum(log.no_of_hours for log in logs)  # Aggregate total logged hours

    def validate(self, data):
        ongoing = data.get('ongoing', False)

        # Ensure required fields based on 'ongoing' status
        if ongoing:
            if not data.get('days_of_week'):
                raise serializers.ValidationError("Days of the week must be specified for ongoing opportunities.")
            if data.get('opportunity_date') is not None:
                raise serializers.ValidationError("Ongoing opportunities must not have an opportunity date.")
            if data.get('slots') is not None:
                raise serializers.ValidationError("Ongoing opportunities cannot have slots.")
        else:
            if 'opportunity_date' not in data or data['opportunity_date'] is None:
                raise serializers.ValidationError("Opportunity date is required for one-time opportunities.")
            if 'opportunity_time_from' not in data or 'opportunity_time_to' not in data:
                raise serializers.ValidationError("Time range (from and to) is required for one-time opportunities.")
            if 'slots' not in data or data['slots'] is None:
                raise serializers.ValidationError("Slots must be set for one-time opportunities.")

        # Validate application deadline
        if data.get('application_deadline'):
            if ongoing:
                raise serializers.ValidationError("Application deadline must be null for ongoing opportunities.")
            if data['application_deadline'] >= data.get('opportunity_date', data['application_deadline']):
                raise serializers.ValidationError("Application deadline must be before the opportunity date.")

        # Validate `requirements` (Must have at least 1 skill from predefined skills)
        valid_skills = [choice[0] for choice in VolunteerOpportunity.SKILLS_CHOICES]
        if 'requirements' in data:
            if not isinstance(data['requirements'], list) or len(data['requirements']) == 0:
                raise serializers.ValidationError("At least one skill must be provided in the requirements.")
            if any(skill not in valid_skills for skill in data['requirements']):
                raise serializers.ValidationError(f"Invalid skill(s) in requirements. Must be one of: {valid_skills}.")

        # Validate `area_of_work`
        valid_fields = [choice[0] for choice in VolunteerOpportunity.FIELDS_OF_INTEREST_CHOICES]
        if data.get('area_of_work') not in valid_fields:
            raise serializers.ValidationError(f"Area of work must be one of {valid_fields}.")

        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authenticated request required.")

        if not request.user.is_organization():
            raise serializers.ValidationError("Only organizations can create opportunities.")

        try:
            organization = Organization.objects.get(account=request.user)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organization not found.")

        validated_data["organization"] = organization

        return super().create(validated_data)
    
class VolunteerOpportunityApplicationSerializer(serializers.ModelSerializer):
    volunteer_opportunity = VolunteerOpportunitySerializer(read_only=True)
    volunteer_opportunity_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerOpportunity.objects.all(), source='volunteer_opportunity', write_only=True
    )
    class Meta:
        model = VolunteerOpportunityApplication
        fields = '__all__'

    def validate(self, data):
        opportunity = data.get('volunteer_opportunity', getattr(self.instance, 'volunteer_opportunity', None))
    
        if not opportunity:
            raise serializers.ValidationError("Volunteer opportunity is required.")

        as_group = data.get('as_group', getattr(self.instance, 'as_group', False))
        no_of_additional_volunteers = data.get('no_of_additional_volunteers', getattr(self.instance, 'no_of_additional_volunteers', 0))

        # Check if opportunity has available slots (only for one-time opportunities)
        if not opportunity.ongoing and opportunity.slots is not None:
            if opportunity.slots < (1 + no_of_additional_volunteers):
                raise serializers.ValidationError("Not enough slots available for this opportunity.")

        # Ensure valid group application constraints
        if as_group and no_of_additional_volunteers < 1:
            raise serializers.ValidationError("Group applications must have at least one additional volunteer.")
        if not as_group and no_of_additional_volunteers != 0:
            raise serializers.ValidationError("Number of additional volunteers must be zero if applying alone.")

        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        new_status = validated_data.get("application_status", instance.application_status)
        opportunity = instance.volunteer_opportunity

        # If application is changing from pending → accepted, deduct slots (only if slots are limited)
        if new_status == "accepted" and instance.application_status != "accepted":
            if not opportunity.ongoing and opportunity.slots is not None:
                total_slots_needed = 1 + instance.no_of_additional_volunteers
                if opportunity.slots < total_slots_needed:
                    raise serializers.ValidationError("Not enough slots available for this opportunity.")
                opportunity.slots -= total_slots_needed
                opportunity.save()

        # Prevent modifications of already accepted applications
        if instance.application_status == "accepted" and new_status != "accepted":
            raise serializers.ValidationError("Cannot modify an already accepted application.")

        return super().update(instance, validated_data)
    
class VolunteerEngagementSerializer(serializers.ModelSerializer):
    volunteer_opportunity_application = VolunteerOpportunityApplicationSerializer(read_only=True)
    volunteer_opportunity_application_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerOpportunityApplication.objects.all(), source='volunteer_opportunity_application', write_only=True
    )
    class Meta:
        model = VolunteerEngagement
        fields = '__all__'
        read_only_fields = ['organization', 'volunteer', 'start_date', 'created_at']

    # Ensures:
    # The engagement can only be created if the application status is 'accepted'.
    # The engagement cannot be marked 'completed' if required logs are not done.
    # The end date cannot be before the start date.
    # Completed engagements must have all session engagements completed.
    def validate(self, data):
        request = self.context.get("request", None)

        # Prevent engagement creation if the application is not accepted
        application = data.get('volunteer_opportunity_application', self.instance.volunteer_opportunity_application if self.instance else None)
        if application and application.application_status != "accepted":
            raise serializers.ValidationError("Volunteer engagement must be created from an accepted application.")

        # Ensure completed/cancelled engagements have an end date
        engagement_status = data.get("engagement_status", self.instance.engagement_status if self.instance else None)
        if engagement_status in ["completed", "cancelled"] and "end_date" in data:
            if data["end_date"] and data["end_date"] < self.instance.start_date:
                raise serializers.ValidationError("End date cannot be before the start date.")

        return data

    # Automatically set organization and volunteer from application.
    def create(self, validated_data):
        application = validated_data['volunteer_opportunity_application']
        validated_data['organization'] = application.volunteer_opportunity.organization
        validated_data['volunteer'] = application.volunteer

        return super().create(validated_data)

    # Automatically set end_date when engagement is marked 'completed' or 'cancelled'.
    def update(self, instance, validated_data):
        new_status = validated_data.get("engagement_status", instance.engagement_status)
        opportunity = instance.volunteer_opportunity_application.volunteer_opportunity

        if new_status in ["completed", "cancelled"] and instance.engagement_status != new_status:
            validated_data["end_date"] = now().date()

            # Re-increment slots when engagement is canceled
            if new_status == "cancelled" and not opportunity.ongoing and opportunity.slots is not None:
                total_slots_to_restore = 1 + instance.volunteer_opportunity_application.no_of_additional_volunteers
                opportunity.slots += total_slots_to_restore
                opportunity.save()

        return super().update(instance, validated_data)
    
class VolunteerOpportunitySessionSerializer(serializers.ModelSerializer):
    opportunity = VolunteerOpportunitySerializer(read_only=True)
    opportunity_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerOpportunity.objects.all(), source='opportunity', write_only=True
    )
    
    class Meta:
        model = VolunteerOpportunitySession
        fields = '__all__'

    # Custom validations for session creation and updates.
    def validate(self, data):
        opportunity = data["opportunity"] if "opportunity" in data else self.instance.opportunity
        
        # Ensure sessions can only be created for ongoing opportunities
        if not opportunity.ongoing:
            raise serializers.ValidationError("Sessions can only be created for ongoing opportunities.")

        # Ensure session start time is before end time
        if data.get("session_start_time") and data.get("session_end_time"):
            if data["session_start_time"] >= data["session_end_time"]:
                raise serializers.ValidationError("Session start time must be before end time.")

        # Prevent modifications if session is completed or cancelled
        if self.instance and self.instance.status in ["completed", "cancelled"]:
            raise serializers.ValidationError("Cannot modify a session that is completed or cancelled.")

        # Ensure slots are positive if defined
        if data.get("slots") is not None and data["slots"] < 1:
            raise serializers.ValidationError("Slots must be a positive integer if set.")

        return data

    # Handle session creation, ensuring opportunity is properly linked.
    def create(self, validated_data):
        return super().create(validated_data)
    
    # If session status changes to 'completed', it should trigger engagement logs.
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", instance.status)

        # If session is marked as completed, trigger engagement logs (handled in API)
        if old_status != "completed" and new_status == "completed":
            # Logic to trigger engagement logs here (handled via API) to IMPLEMENT LATER
            pass

        return super().update(instance, validated_data)
    
class VolunteerSessionEngagementSerializer(serializers.ModelSerializer):
    volunteer_engagement = VolunteerEngagementSerializer(read_only=True)
    volunteer_engagement_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerEngagement.objects.all(), source='volunteer_engagement', write_only=True
    )
    session = VolunteerOpportunitySessionSerializer(read_only=True)
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerOpportunitySession.objects.all(), source='session', write_only=True
    )
    class Meta:
        model = VolunteerSessionEngagement
        fields = '__all__'

    def validate(self, data):
        volunteer_engagement = data["volunteer_engagement"] if "volunteer_engagement" in data else self.instance.volunteer_engagement
        session = data["session"] if "session" in data else self.instance.session
        new_status = data.get("status", "cant_go")

        # Ensure session belongs to the same opportunity as the engagement
        if session.opportunity != volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity:
            raise serializers.ValidationError("Session does not belong to the same opportunity as the engagement.")

        # Ensure session slots are not full if setting status to 'can_go'
        if new_status == "can_go" and session.slots is not None:
            current_attendees = VolunteerSessionEngagement.objects.filter(session=session, status="can_go").count()
            if current_attendees >= session.slots:
                raise serializers.ValidationError("This session is fully booked.")

        return data
    
    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        new_status = validated_data.get("status", instance.status)
        old_status = instance.status

        # Prevent cancelling last minute
        if new_status == "cant_go" and instance.session.session_date <= now().date():
            raise serializers.ValidationError("You cannot cancel your attendance on the day of the session.")
        
        # Handle slot updates if session has limited slots
        session = instance.session
        if session.slots is not None:
            if old_status == "cant_go" and new_status == "can_go":
                session.slots -= 1  # Decrement slots
            elif old_status == "can_go" and new_status == "cant_go":
                session.slots += 1  # Increment slots
            
            session.save()  # Save the updated slot count

        return super().update(instance, validated_data)
    
class VolunteerEngagementLogSerializer(serializers.ModelSerializer):
    volunteer_engagement = VolunteerEngagementSerializer(read_only=True)
    volunteer_engagement_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerEngagement.objects.all(), source='volunteer_engagement', write_only=True
    )
    session = VolunteerSessionEngagementSerializer(read_only=True, required=False, allow_null=True)
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerSessionEngagement.objects.all(), source='session', write_only=True, required=False, allow_null=True
    )
    class Meta:
        model = VolunteerEngagementLog
        fields = '__all__'

    def validate(self, data):
        volunteer_engagement = data.get("volunteer_engagement") if "volunteer_engagement" in data else self.instance.volunteer_engagement
        session_engagement = data.get("session", None) if "session" in data else None
        no_of_hours = data.get("no_of_hours", self.instance.no_of_hours if self.instance else 0)
        new_status = data.get("status", self.instance.status if self.instance else "pending")
        opportunity = volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity

        # If session engagement exists, extract the session object
        session = session_engagement.session if session_engagement else None

        # Ensure logs cannot be created for future sessions/opportunities
        if session and session.session_date > now().date():
            raise serializers.ValidationError("You cannot create logs for a session that has not yet happened.")
        elif not session and opportunity.opportunity_date and opportunity.opportunity_date > now().date():
            raise serializers.ValidationError("You cannot create logs for an opportunity that has not yet happened.")

        # Prevent duplicate logs for the same engagement/session - NB: Model constraints already prevent duplicate logs
        existing_log = VolunteerEngagementLog.objects.filter(
            volunteer_engagement=volunteer_engagement,
            session=session_engagement  # Ensuring we're filtering by session_engagement
        ).exclude(pk=self.instance.pk if self.instance else None).exists()

        if existing_log:
            raise serializers.ValidationError("You have already logged hours for this engagement.")

        # Validate logged hours do not exceed session or opportunity duration
        if session:
            session_duration = (
                session.session_end_time.hour + session.session_end_time.minute / 60
            ) - (session.session_start_time.hour + session.session_start_time.minute / 60)
            if no_of_hours > session_duration:
                raise serializers.ValidationError("Logged hours exceed session duration.")
        else:
            # If one-time opportunity, else if ongoing and volunteer has logged hours without a session, ignore duration check
            if opportunity.opportunity_time_from and opportunity.opportunity_time_to:
                opportunity_duration = (
                    opportunity.opportunity_time_to.hour + opportunity.opportunity_time_to.minute / 60
                ) - (opportunity.opportunity_time_from.hour + opportunity.opportunity_time_from.minute / 60)
                if no_of_hours > opportunity_duration:
                    raise serializers.ValidationError("Logged hours exceed opportunity duration.")

        # Ensure no_of_hours cannot be negative
        if no_of_hours <= 0:
            raise serializers.ValidationError("Logged hours must be greater than zero.")
        
        return data

    # If log is for an ongoing opportunity without a session, mark as 'pending' by default. Otherwise, log is created as usual.
    def create(self, validated_data):
        log = VolunteerEngagementLog(**validated_data)
        if not validated_data.get("session") and log.volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity.ongoing:
            log.status = "pending"
        log.save()
        return log

    def update(self, instance, validated_data):
        request = self.context.get("request")
        new_status = validated_data.get("status", instance.status)

        # Check if account changing statusis organization check is here and is organization which created the opportunity to be done in API
        if new_status in ["approved", "rejected"]:
            if not request or request.user.user_type != "organization":
                raise serializers.ValidationError("Only organizations can approve or reject logs.")
        
        # Prevent modification of approved logs
        if instance.status == "approved" and new_status != "approved":
            raise serializers.ValidationError("Approved logs cannot be modified.")

        return super().update(instance, validated_data)
