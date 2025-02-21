from rest_framework import serializers
from .models import Volunteer, Organization, Following
from accounts_notifs.serializers import AccountSerializer

class VolunteerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volunteer
        fields = ["first_name", "last_name", "dob", "bio", "profile_img", "followers"]

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["organization_name", "organization_description", "organization_address", "organization_website", "organization_profile_img", "followers"]

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