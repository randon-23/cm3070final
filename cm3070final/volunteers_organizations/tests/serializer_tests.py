from django.test import TestCase
from rest_framework.exceptions import ValidationError
from ..serializers import VolunteerSerializer, OrganizationSerializer, FollowingCreateSerializer, EndorsementSerializer, StatusPostSerializer, VolunteerMatchingPreferencesSerializer, OrganizationPreferencesSerializer
from ..models import Volunteer, Organization, Following, VolunteerMatchingPreferences, OrganizationPreferences
from accounts_notifs.models import Account
from datetime import date
from unittest.mock import Mock

class TestVolunteerSerializer(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35612345678"
        )
        self.volunteer = Volunteer.objects.create(
            account=self.account,
            first_name="John",
            last_name="Doe",
            dob=date(1990, 1, 1),
            bio="Passionate about helping others",
            followers=100
        )

    # Ensure the serializer outputs correct data
    def test_serialize_volunteer(self):
        
        serializer = VolunteerSerializer(self.volunteer)
        expected_data = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "bio": "Passionate about helping others",
            "profile_img": None,
            "followers": 100,
        }
        self.assertEqual(serializer.data, expected_data)

class TestOrganizationSerializer(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email_address="org@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+35687654321"
        )
        self.organization = Organization.objects.create(
            account=self.account,
            organization_name="Helping Hands",
            organization_description="A non-profit focused on community service.",
            organization_address={"street": "123 Charity St", "city": "Valletta"},
            organization_website="https://helpinghands.org",
            followers=50
        )

    # Ensure the serializer outputs correct data
    def test_serialize_organization(self):
        
        serializer = OrganizationSerializer(self.organization)
        expected_data = {
            "organization_name": "Helping Hands",
            "organization_description": "A non-profit focused on community service.",
            "organization_address": {"street": "123 Charity St", "city": "Valletta"},
            "organization_website": "https://helpinghands.org",
            "organization_profile_img": None,
            "followers": 50,
        }
        self.assertEqual(serializer.data, expected_data)

class TestFollowingCreateSerializer(TestCase):
    def setUp(self):
        self.follower = Account.objects.create_user(
            email_address="follower@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35699998888"
        )
        self.volunteer_followee = Account.objects.create_user(
            email_address="volunteer_followee@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35611112222"
        )
        self.organization_followee = Account.objects.create_user(
            email_address="organization_followee@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+35633334444"
        )

        self.follower_volunteer = Volunteer.objects.create(account=self.follower, first_name="John", last_name="Doe", dob=date(1990, 1, 1))
        self.volunteer = Volunteer.objects.create(account=self.volunteer_followee, first_name="Jane", last_name="Smith", dob=date(1995, 5, 5))
        self.organization = Organization.objects.create(account=self.organization_followee, organization_name="EcoSave", organization_description="Environmental charity.")

        self.mock_request = Mock()
        self.mock_request.user = self.follower

    # Ensure a valid follow request for a volunteer works
    def test_create_following_valid_volunteer(self):
        data = {"followed_volunteer": self.volunteer}
        serializer = FollowingCreateSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        following = serializer.save()
        self.assertEqual(following.follower, self.follower)
        self.assertEqual(following.followed_volunteer, self.volunteer)
        self.assertIsNone(following.followed_organization)

    # Ensure a valid follow request for an organization works
    def test_create_following_valid_organization(self):
        data = {"followed_organization": self.organization}
        serializer = FollowingCreateSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        following = serializer.save()
        self.assertEqual(following.follower, self.follower)
        self.assertEqual(following.followed_organization, self.organization)
        self.assertIsNone(following.followed_volunteer)

    # Ensure an error is raised when trying to follow both at the same time
    def test_following_both_volunteer_and_organization_fails(self):
        data = {"followed_volunteer": self.volunteer, "followed_organization": self.organization}
        serializer = FollowingCreateSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Cannot follow both a volunteer and an organization.", str(error.exception))

    # Ensure a user cannot follow themselves
    def test_following_self_fails(self):
        data = {"followed_volunteer": self.follower_volunteer}
        serializer = FollowingCreateSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Cannot follow yourself", str(error.exception))

    # Ensure organizations cannot follow anyone
    def test_organization_cannot_follow(self):
        org_follower = Account.objects.create_user(
            email_address="org_follower@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+35655556666"
        )
        self.mock_request.user = org_follower
        data = {"followed_volunteer": self.volunteer}
        serializer = FollowingCreateSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Organizations cannot follow", str(error.exception))

class TestEndorsementSerializer(TestCase):
    def setUp(self):
        self.volunteer1 = Account.objects.create_user(
            email_address="vol1@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35699998888"
        )
        self.volunteer2 = Account.objects.create_user(
            email_address="vol2@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35688887777"
        )
        self.organization = Account.objects.create_user(
            email_address="org@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+35677776666"
        )

        # Mock request
        self.mock_request = Mock()
        self.mock_request.user = self.volunteer1

    def test_create_valid_endorsement_volunteer_to_volunteer(self):
        data = {"receiver": self.volunteer2.account_uuid, "endorsement": "Hard worker!"}
        serializer = EndorsementSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        endorsement = serializer.save()
        self.assertEqual(endorsement.giver, self.volunteer1)
        self.assertEqual(endorsement.receiver, self.volunteer2)
        self.assertEqual(endorsement.endorsement, "Hard worker!")

    def test_create_valid_endorsement_org_to_volunteer(self):
        self.mock_request.user = self.organization
        data = {"receiver": self.volunteer1.account_uuid, "endorsement": "Reliable volunteer!"}
        serializer = EndorsementSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        endorsement = serializer.save()
        self.assertEqual(endorsement.giver, self.organization)
        self.assertEqual(endorsement.receiver, self.volunteer1)

    def test_organization_cannot_endorse_organization(self):
        self.mock_request.user = self.organization
        data = {"receiver": self.organization.account_uuid, "endorsement": "Great organization!"}
        serializer = EndorsementSerializer(data=data, context={"request": self.mock_request})
        
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Organizations cannot endorse each other.", str(error.exception))

    def test_cannot_endorse_self(self):
        data = {"receiver": self.volunteer1.account_uuid, "endorsement": "I'm amazing!"}
        serializer = EndorsementSerializer(data=data, context={"request": self.mock_request})
        
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Cannot endorse yourself.", str(error.exception))

class TestStatusPostSerializer(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            email_address="user@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35655554444"
        )

        # Mock request
        self.mock_request = Mock()
        self.mock_request.user = self.user

    def test_create_valid_status_post(self):
        data = {"content": "This is my first status update!"}
        serializer = StatusPostSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        status_post = serializer.save()
        self.assertEqual(status_post.author, self.user)
        self.assertEqual(status_post.content, "This is my first status update!")

    def test_create_status_post_fails_with_empty_content(self):
        data = {"content": ""}
        serializer = StatusPostSerializer(data=data, context={"request": self.mock_request})
        
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("This field may not be blank.", str(error.exception))

class TestVolunteerMatchingPreferencesSerializer(TestCase):
    def setUp(self):
        self.volunteer_account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35699998888"
        )
        self.volunteer = Volunteer.objects.create(
            account=self.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 4, 12)
        )

        self.mock_request = Mock()
        self.mock_request.user = self.volunteer_account

    # Ensure valid data is saved correctly
    def test_create_valid_volunteer_preferences(self):
        data = {
            "availability": ["monday", "wednesday", "friday"],
            "preferred_work_types": "both",
            "preferred_duration": ["short-term", "medium-term"],
            "fields_of_interest": ["education", "health"],
            "skills": ["communication", "leadership"],
            "languages": ["English", "French"],
            "smart_matching_enabled": True
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        preferences = serializer.save()
        self.assertEqual(preferences.volunteer, self.volunteer)
        self.assertEqual(preferences.availability, ["monday", "wednesday", "friday"])
        self.assertEqual(preferences.preferred_work_types, "both")

    # Ensure invalid availability values are rejected
    def test_invalid_availability(self):
        data = {
            "availability": ["monday", "invalid_day"]
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Invalid availability day(s) provided.", str(error.exception))

    # Ensure more than 5 fields of interest are rejected
    def test_too_many_fields_of_interest(self):
        data = {
            "fields_of_interest": ["education", "health", "sports", "arts", "community", "technology"]
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("You can select up to 5 fields of interest.", str(error.exception))

    # Ensure more than 10 skills are rejected
    def test_too_many_skills(self):
        data = {
            "skills": ["communication", "leadership", "teamwork", "writing", "marketing", "teaching",
                       "public speaking", "photography", "videography", "coding", "event planning"]
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("You can select up to 10 skills.", str(error.exception))

    # Ensure duplicate preferences creation fails
    def test_duplicate_preferences_creation(self):
        self.mock_request.method = "POST"
        VolunteerMatchingPreferences.objects.create(
            volunteer=self.volunteer,
            availability=["monday", "tuesday"],
            preferred_work_types="online",
            preferred_duration=["short-term"],
            fields_of_interest=["health"],
            skills=["teamwork"],
            languages=["Spanish"],
            smart_matching_enabled=True
        )

        data = {
            "availability": ["monday", "wednesday"],
            "preferred_work_types": "both",
            "preferred_duration": ["short-term", "medium-term"],
            "fields_of_interest": ["education"],
            "skills": ["communication"],
            "languages": ["English"]
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Volunteer Matching Preferences already exist for this volunteer.", str(error.exception))

    def test_create_valid_volunteer_preferences_with_location(self):
        data = {
            "availability": ["monday", "wednesday"],
            "preferred_work_types": "both",
            "preferred_duration": ["short-term"],
            "fields_of_interest": ["education"],
            "skills": ["communication"],
            "languages": ["English"],
            "location": {
                "lat": 35.8995,
                "lon": 14.5146,
                "city": "Valletta",
                "formatted_address": "Valletta, Malta"
            }
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        preferences = serializer.save()
        self.assertEqual(preferences.volunteer, self.volunteer)
        self.assertEqual(preferences.location["city"], "Valletta")

    # Ensure invalid location data is rejected
    def test_invalid_location_data(self):
        data = {
            "location": "invalid_location_format"  # Should be a dict
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Location must be a dictionary.", str(error.exception))

    # Ensure missing required location fields fail validation
    def test_missing_required_location_fields(self):
        data = {
            "location": {"lat": 35.8995, "lon": 14.5146}  # Missing 'city' and 'formatted_address'
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Location must contain", str(error.exception))

    # Ensure duplicate volunteer preferences creation fails (with location)
    def test_duplicate_volunteer_preferences_creation_with_location(self):
        self.mock_request.method = "POST"
        VolunteerMatchingPreferences.objects.create(
            volunteer=self.volunteer,
            availability=["monday", "tuesday"],
            preferred_work_types="online",
            preferred_duration=["short-term"],
            fields_of_interest=["health"],
            skills=["teamwork"],
            languages=["Spanish"],
            smart_matching_enabled=True,
            location={
                "lat": 35.8995,
                "lon": 14.5146,
                "city": "Valletta",
                "formatted_address": "Valletta, Malta"
            }
        )

        data = {
            "availability": ["monday", "wednesday"],
            "preferred_work_types": "both",
            "preferred_duration": ["short-term", "medium-term"],
            "fields_of_interest": ["education"],
            "skills": ["communication"],
            "languages": ["English"],
            "location": {
                "lat": 36.9000,
                "lon": 15.5151,
                "city": "Mdina",
                "formatted_address": "Mdina, Malta"
            }
        }
        serializer = VolunteerMatchingPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Volunteer Matching Preferences already exist for this volunteer.", str(error.exception))

class TestOrganizationPreferencesSerializer(TestCase):
    def setUp(self):
        self.organization_account = Account.objects.create_user(
            email_address="organization@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+35699998888"
        )
        self.organization = Organization.objects.create(
            account=self.organization_account,
            organization_name="Helping Hands",
            organization_address="123 Volunteer St.",
            organization_website="https://helpinghands.org"
        )

        self.mock_request = Mock()
        self.mock_request.user = self.organization_account

    # Ensure valid data is saved correctly
    def test_create_valid_organization_preferences(self):
        data = {
            "enable_volontera_point_opportunities": True,
            "volontera_points_rate": 1.5,
            "location": {
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        preferences = serializer.save()
        self.assertEqual(preferences.organization, self.organization)
        self.assertEqual(preferences.enable_volontera_point_opportunities, True)
        self.assertEqual(preferences.volontera_points_rate, 1.5)
        self.assertEqual(preferences.location["city"], "New York")

    # Ensure invalid location data is rejected
    def test_invalid_location_data(self):
        data = {
            "location": "invalid_location_format"  # Should be a dictionary
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Location must be a dictionary.", str(error.exception))

    # Ensure missing required location fields fail validation
    def test_missing_required_location_fields(self):
        data = {
            "location": {"lat": 40.7128, "lon": -74.0060}  # Missing 'city' and 'formatted_address'
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Location must contain", str(error.exception))

    # Ensure invalid volontera points rate fails validation
    def test_invalid_volontera_points_rate_negative(self):
        data = {
            "volontera_points_rate": -5  # Should be positive
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Volontera points rate must be positive.", str(error.exception))

    def test_invalid_volontera_points_rate_too_large(self):
        data = {
            "volontera_points_rate": 2.0  # Should be max 1.5
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Volontera points rate cannot exceed 1.5.", str(error.exception))

    # Ensure duplicate organization preferences creation fails
    def test_duplicate_preferences_creation(self):
        self.mock_request.method = "POST"
        OrganizationPreferences.objects.create(
            organization=self.organization,
            enable_volontera_point_opportunities=True,
            volontera_points_rate=1.5,
            location={"lat": 40.7128, "lon": -74.0060, "city": "New York", "formatted_address": "New York, NY, USA"}
        )

        data = {
            "enable_volontera_point_opportunities": False,
            "volontera_points_rate": 1.2,
            "location": {
                "lat": 36.9000,
                "lon": 15.5151,
                "city": "Mdina",
                "formatted_address": "Mdina, Malta"
            }
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})
        with self.assertRaises(ValidationError) as error:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Organization Preferences already exist for this organization.", str(error.exception))

    # Ensure organization preferences can be created with location
    def test_create_organization_preferences_with_location(self):
        data = {
            "enable_volontera_point_opportunities": True,
            "volontera_points_rate": 1.2,
            "location": {
                "lat": 36.9000,
                "lon": 15.5151,
                "city": "Mdina",
                "formatted_address": "Mdina, Malta"
            }
        }
        serializer = OrganizationPreferencesSerializer(data=data, context={"request": self.mock_request})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        preferences = serializer.save()
        self.assertEqual(preferences.organization, self.organization)
        self.assertEqual(preferences.location["city"], "Mdina")
        self.assertEqual(preferences.enable_volontera_point_opportunities, True)
        self.assertEqual(preferences.volontera_points_rate, 1.2)