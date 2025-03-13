from rest_framework import serializers
from .models import Volunteer, Organization, Following, Endorsement, StatusPost, VolunteerMatchingPreferences, OrganizationPreferences
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.urls import reverse

Account = get_user_model()

class VolunteerSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = Volunteer
        fields = ["first_name", "last_name", "dob", "bio", "profile_img", "followers", "profile_url"]

    def get_profile_url(self, obj):
        return reverse("volunteers_organizations:profile", kwargs={"account_uuid": obj.account.account_uuid})

class OrganizationSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["organization_name", "organization_description", "organization_address", "organization_website", "organization_profile_img", "followers", "profile_url"]

    def get_profile_url(self, obj):
        return reverse("volunteers_organizations:profile", kwargs={"account_uuid": obj.account.account_uuid})
    
# Serializer to get volunteer and organization data along with account data
class UserDataSerializer(serializers.HyperlinkedModelSerializer):
    email_address = serializers.EmailField()
    user_type = serializers.SerializerMethodField()
    volunteer = VolunteerSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Account
        fields = ["account_uuid", "email_address", "user_type", "volunteer", "organization"]
        extra_kwargs = {
            "url": {"view_name": "volunteers_organizations:profile", "lookup_field": "account_uuid"}
        }

    def get_user_type(self, obj):
        if hasattr(obj, "volunteer"):
            return "Volunteer"
        elif hasattr(obj, "organization"):
            return "Organization"
        return "Unknown"

class FollowingCreateSerializer(serializers.ModelSerializer):
    followed_volunteer = serializers.PrimaryKeyRelatedField(
        queryset=Volunteer.objects.all(), required=False, allow_null=True
    )
    followed_organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Following
        fields = ['follower', 'followed_volunteer', 'followed_organization', 'created_at']
        read_only_fields = ['follower', 'created_at']

    def validate(self, data):
        follower = self.context['request'].user

        followed_volunteer = data.get('followed_volunteer')
        followed_organization = data.get('followed_organization')

        if not followed_volunteer and not followed_organization:
            raise serializers.ValidationError("You must follow either a volunteer or an organization.")
        
        if followed_volunteer and followed_organization:
            raise serializers.ValidationError("Cannot follow both a volunteer and an organization.")
            
        if follower.is_organization():
            raise serializers.ValidationError("Organizations cannot follow")
        
        if follower.volunteer:
            if follower.volunteer == followed_volunteer or follower.volunteer == followed_organization:
                raise serializers.ValidationError("Cannot follow yourself")
        
        return data
    
    def create(self, validated_data):
        follower = self.context['request'].user 

        if validated_data.get('followed_volunteer'):
            return Following.objects.create(follower=follower, followed_volunteer=validated_data['followed_volunteer'])
        else:
            return Following.objects.create(follower=follower, followed_organization=validated_data['followed_organization'])
        
class EndorsementSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    giver = UserDataSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = ["id", "giver", "receiver", "endorsement", "created_at"]
        read_only_fields = ["id", "giver", "created_at"]

    def get_created_at(self, obj):
        if isinstance(obj.created_at, str):
            return parse_datetime(obj.created_at)
        return obj.created_at
    
    def validate(self, data):
        giver = self.context["request"].user

        if giver.is_organization() and data["receiver"].is_organization():
            raise serializers.ValidationError("Organizations cannot endorse each other.")
        
        if giver == data["receiver"]:
            raise serializers.ValidationError("Cannot endorse yourself.")
        
        return data

    def create(self, validated_data):
        giver = self.context["request"].user
        validated_data["giver"] = giver
        return super().create(validated_data)

class StatusPostSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    author = UserDataSerializer(read_only=True)

    # Convert string to datetime object
    def get_created_at(self, obj):
        if isinstance(obj.created_at, str):
            return parse_datetime(obj.created_at)
        return obj.created_at
    
    class Meta:
        model = StatusPost
        fields = ["id", "author", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Status post cannot be empty.", code="blank")
        return value

    def create(self, validated_data):
        author = self.context["request"].user
        validated_data["author"] = author
        return super().create(validated_data)
    
class VolunteerMatchingPreferencesSerializer(serializers.ModelSerializer):
    volunteer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = VolunteerMatchingPreferences
        fields = '__all__'

    def validate(self, data):
        request = self.context['request']
        volunteer = Volunteer.objects.get(account=self.context['request'].user)  # Get account from request

        if VolunteerMatchingPreferences.objects.filter(volunteer=volunteer).exists() and request.method == 'POST':
            raise serializers.ValidationError("Volunteer Matching Preferences already exist for this volunteer.")

        data['volunteer'] = volunteer
        return data

    def validate_location(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Location must be a dictionary.")
        required_keys = {'lat', 'lon', 'city', 'formatted_address'}
        if not required_keys.issubset(value.keys()):
            raise serializers.ValidationError(f"Location must contain: {required_keys}.")
        return value
    
    def validate_availability(self, value):
        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
        if not isinstance(value, list):
            raise serializers.ValidationError("Availability must be a list.")
        if any(day.lower() not in valid_days for day in value):
            raise serializers.ValidationError("Invalid availability day(s) provided.")
        return value

    def validate_fields_of_interest(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("You can select up to 5 fields of interest.")
        return value

    def validate_skills(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("You can select up to 10 skills.")
        return value

    def validate_languages(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Languages must be a list.")
        return value

    def create(self, validated_data):
        return super().create(validated_data)
    
class OrganizationPreferencesSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OrganizationPreferences
        fields = '__all__'

    def validate(self, data):
        request = self.context['request']
        organization = Organization.objects.get(account=self.context['request'].user)
        
        if OrganizationPreferences.objects.filter(organization=organization).exists() and request.method == 'POST':
            raise serializers.ValidationError("Organization Preferences already exist for this organization.")

        data['organization'] = organization
        return data

    def validate_location(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Location must be a dictionary.")
        required_keys = {'lat', 'lon', 'city', 'formatted_address'}
        if not required_keys.issubset(value.keys()):
            raise serializers.ValidationError(f"Location must contain: {required_keys}.")
        return value

    def validate_volontera_points_rate(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Volontera points rate must be positive.")
        if value > 1.5:
            raise serializers.ValidationError("Volontera points rate cannot exceed 1.5.")
        return value

    def create(self, validated_data):
        return super().create(validated_data)