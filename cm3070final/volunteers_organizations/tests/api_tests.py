from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Volunteer, Organization, Following, Endorsement, StatusPost, VolunteerMatchingPreferences, OrganizationPreferences
from accounts_notifs.models import Account
from django.urls import reverse

Account = get_user_model()

class TestFollowUnfollowAPI(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user who will be the follower
        cls.follower = Account.objects.create_user(
            email_address="follower@example.com",
            password="securePassword1!",
            user_type="volunteer",
            contact_number="+35612345678"
        )
        cls.follower_volunteer = Volunteer.objects.create(
            account=cls.follower,
            first_name="Follower",
            last_name="User",
            dob="1990-01-01"
        )

        # Create another user to be followed (volunteer)
        cls.followed_volunteer = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="securePassword1!",
            user_type="volunteer",
            contact_number="+35687654321"
        )
        cls.volunteer_profile = Volunteer.objects.create(
            account=cls.followed_volunteer,
            first_name="Volunteer",
            last_name="User",
            dob="1995-06-15"
        )

        # Create another user to be followed (organization)
        cls.followed_organization = Account.objects.create_user(
            email_address="org@example.com",
            password="securePassword1!",
            user_type="organization",
            contact_number="+35611223344"
        )
        cls.organization_profile = Organization.objects.create(
            account=cls.followed_organization,
            organization_name="Helping Hands",
            organization_description="A non-profit organization",
            organization_address={}
        )
    
    def setUp(self):
        self.client.force_authenticate(user=self.follower)

    # Ensure that a new account has zero followers
    def test_get_all_followers_initially_zero(self):
        url = reverse('volunteers_organizations:get_all_followers', args=[self.followed_volunteer.account_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['followers'], 0)

    # Test that the authenticated user can follow a volunteer
    def test_create_following(self):
        url = reverse('volunteers_organizations:create_following', args=[self.followed_volunteer.account_uuid])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the Following object was created
        self.assertTrue(Following.objects.filter(follower=self.follower, followed_volunteer=self.volunteer_profile).exists())

    # Test that the authenticated user can follow an organization
    def test_create_following_organization(self):
        url = reverse('volunteers_organizations:create_following', args=[self.followed_organization.account_uuid])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the Following object was created
        self.assertTrue(Following.objects.filter(follower=self.follower, followed_organization=self.organization_profile).exists())

    # Ensure that follower count updates correctly after following
    def test_get_all_followers_after_following(self):
        Following.objects.create(follower=self.follower, followed_volunteer=self.volunteer_profile)
        
        url = reverse('volunteers_organizations:get_all_followers', args=[self.followed_volunteer.account_uuid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['followers'], 1)

    # Ensure the API correctly identifies when a user is following another
    def test_get_following_true(self):
        Following.objects.create(follower=self.follower, followed_volunteer=self.volunteer_profile)

        url = reverse('volunteers_organizations:get_following', args=[self.followed_volunteer.account_uuid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_following'])
    
    # Ensure the API correctly identifies when a user is NOT following another
    def test_get_following_false(self):
        url = reverse('volunteers_organizations:get_following', args=[self.followed_volunteer.account_uuid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_following'])
    
    # Ensure that a user can unfollow another user
    def test_delete_following(self):
        following = Following.objects.create(follower=self.follower, followed_volunteer=self.volunteer_profile)
        
        url = reverse('volunteers_organizations:delete_following', args=[self.followed_volunteer.account_uuid])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the Following object was deleted
        self.assertFalse(Following.objects.filter(pk=following.pk).exists())

    # Ensure that trying to unfollow when not following returns a 404
    def test_delete_following_not_exists(self):
        url = reverse('volunteers_organizations:delete_following', args=[self.followed_volunteer.account_uuid])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestEndorsementAPI(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer1 = Account.objects.create_user(
            email_address="vol1@example.com", 
            password="Securepass123!", 
            user_type="volunteer",
            contact_number="+356123456778"    
        )
        cls.volunteer2 = Account.objects.create_user(
            email_address="vol2@example.com", 
            password="Securepass123!", 
            user_type="volunteer",
            contact_number="+356123456779"    
        )
        cls.organization = Account.objects.create_user(
            email_address="org@example.com", 
            password="Securepass123!", 
            user_type="organization",
            contact_number="+356123456780"
        )
        cls.volunteer1_profile = Volunteer.objects.create(
            account=cls.volunteer1,
            first_name="John",
            last_name="Doe",
            dob="1995-06-15"
        )
        cls.volunteer2_profile = Volunteer.objects.create(
            account=cls.volunteer2,
            first_name="Jane",
            last_name="Smith",
            dob="1996-07-20"
        )
        cls.organization_profile = Organization.objects.create(
            account=cls.organization,
            organization_name="Helping Hands",
            organization_description="A non-profit org",
            organization_address={
                'raw': '123 Greenway Blvd, Springfield, US',
                'street_number': '123',
                'route': 'Greenway Blvd',
                'locality': 'Springfield',
                'postal_code': '12345',
                'state': 'Illinois',
                'state_code': 'IL',
                'country': 'United States',
                'country_code': 'US'
            }
        )
    def setUp(self):
        self.client.force_authenticate(user=self.volunteer1)

    # Test valid endorsement from volunteer to volunteer
    def test_create_valid_endorsement(self):
        url = reverse('volunteers_organizations:create_endorsement', args=[self.volunteer2.account_uuid])
        data = {"endorsement": "Great work!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Endorsement.objects.filter(giver=self.volunteer1, receiver=self.volunteer2).exists())

    # Test a user cannot endorse themselves
    def test_cannot_endorse_self(self):
        url = reverse('volunteers_organizations:create_endorsement', args=[self.volunteer1.account_uuid])
        data = {"endorsement": "I'm amazing!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test valid endorsement from organization to volunteer
    def test_create_valid_endorsement_org_to_volunteer(self):
        self.client.force_authenticate(user=self.organization)
        url = reverse('volunteers_organizations:create_endorsement', args=[self.volunteer1.account_uuid])
        data = {"endorsement": "Reliable volunteer!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Endorsement.objects.filter(giver=self.organization, receiver=self.volunteer1).exists())

    # Test organizations cannot endorse each other
    def test_organization_cannot_endorse_organization(self):
        self.client.force_authenticate(user=self.organization)
        url = reverse('volunteers_organizations:create_endorsement', args=[self.organization.account_uuid])
        data = {"endorsement": "Great org!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test retrieving endorsements for a user
    def test_get_endorsements(self):
        Endorsement.objects.create(giver=self.volunteer1, receiver=self.volunteer2, endorsement="Hard worker!")
        url = reverse('volunteers_organizations:get_endorsements', args=[self.volunteer2.account_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # Test deleting an endorsement
    def test_delete_endorsement(self):
        endorsement = Endorsement.objects.create(giver=self.volunteer1, receiver=self.volunteer2, endorsement="Great job!")
        url = reverse('volunteers_organizations:delete_endorsement', args=[endorsement.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Endorsement.objects.filter(id=endorsement.id).exists())

class TestStatusPostAPI(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Account.objects.create_user(
            email_address="user@example.com", 
            password="Securepass123!", 
            user_type="volunteer",
            contact_number="+356123456778"
        )
        cls.volunteer = Volunteer.objects.create(
            account=cls.user,
            first_name="John",
            last_name="Doe",
            dob="1995-06-15"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    # Test valid status post creation
    def test_create_valid_status_post(self):
        url = reverse('volunteers_organizations:create_status_post')
        data = {"content": "My first status update!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StatusPost.objects.filter(author=self.user, content="My first status update!").exists())

    # Test empty status post fails
    def test_empty_status_post_fails(self):
        url = reverse('volunteers_organizations:create_status_post')
        data = {"content": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test retrieving all status posts
    def test_get_status_posts(self):
        StatusPost.objects.create(author=self.user, content="Test status")
        url = reverse('volunteers_organizations:get_status_posts', args=[self.user.account_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # Test deleting a status post
    def test_delete_status_post(self):
        status_post = StatusPost.objects.create(author=self.user, content="Test status")
        url = reverse('volunteers_organizations:delete_status_post', args=[status_post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StatusPost.objects.filter(id=status_post.id).exists())

class TestSearchProfilesAPI(APITestCase):
    def setUp(self):
        # Set up test data
        self.user = Account.objects.create_user(
            email_address="testuser@example.com", 
            password="testpassword", 
            user_type="Volunteer",
            contact_number="+35612345678"
        )
        self.client.force_authenticate(user=self.user)

        # Create a volunteer
        self.volunteer = Volunteer.objects.create(
            account=self.user,
            first_name="Adam",
            last_name="Randon",
            bio="I love volunteering!",
            dob="1995-06-15"
        )

        # Create an organization
        self.organization = Organization.objects.create(
            account=Account.objects.create_user(
                email_address="org@example.com", 
                password="testpassword", 
                user_type="Organization"
            ),
            organization_name="Helping Hands",
            organization_description="A non-profit org",
        )

        # URL for search API
        self.search_url = reverse("volunteers_organizations:get_search_profiles")

    # Test searching a volunteer by first name
    def test_search_volunteer_by_first_name(self):
        response = self.client.get(self.search_url, {"q": "Adam"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(v["first_name"] == "Adam" for v in response.data["results"]))

    # Test searching a volunteer by last name
    def test_search_volunteer_by_last_name(self):
        response = self.client.get(self.search_url, {"q": "Randon"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(v["last_name"] == "Randon" for v in response.data["results"]))
    
    # Test searching a volunteer by full name
    def test_search_volunteer_by_full_name(self):
        response = self.client.get(self.search_url, {"q": "Adam Randon"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(v["first_name"] == "Adam" and v["last_name"] == "Randon" for v in response.data["results"]))

    # Test searching an organization by name
    def test_search_organization_by_name(self):
        response = self.client.get(self.search_url, {"q": "Helping Hands"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(org["organization_name"] == "Helping Hands" for org in response.data["results"]))

    # Test that an empty search query returns an empty list
    def test_empty_search_returns_empty_list(self):
        response = self.client.get(self.search_url, {"q": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    # Test that the search endpoint requires authentication
    def test_search_requires_authentication(self):
        self.client.logout()
        response = self.client.get(self.search_url, {"q": "Adam"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test that wrong method returns 405
    def test_wrong_method_returns_405(self):
        response = self.client.post(self.search_url, {"q": "Adam"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class TestVolunteerPreferencesAPI(APITestCase):
    def setUp(self):
        self.volunteer_account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="testpass",
            user_type="volunteer",
            contact_number="+35612345678"
        )
        self.volunteer = Volunteer.objects.create(
            account=self.volunteer_account,
            first_name="John",
            last_name="Doe", 
            dob="1995-06-15" 
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.volunteer_account)

        self.create_volunteer_preferences_url = reverse("volunteers_organizations:create_volunteer_preferences")
        self.get_volunteer_preferences_url = reverse("volunteers_organizations:get_volunteer_preferences")
        self.update_volunteer_preferences_url = reverse("volunteers_organizations:update_volunteer_preferences")

    # Successfully create volunteer preferences
    def test_create_volunteer_preferences_success(self):
        data = {
            "availability": ["monday", "wednesday"],
            "preferred_work_types": "online",
            "preferred_duration": ["short-term"],
            "fields_of_interest": ["education", "community"],
            "skills": ["public speaking", "leadership"],
            "languages": ["English", "Spanish"]
        }
        response = self.client.post(self.create_volunteer_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VolunteerMatchingPreferences.objects.count(), 1)
        self.assertEqual(response.data["data"]["volunteer"], self.volunteer.pk)

    # Attempt to create duplicate preferences (should return 409 Conflict)
    def test_create_duplicate_volunteer_preferences(self):
        VolunteerMatchingPreferences.objects.create(volunteer=self.volunteer)
        response = self.client.post(self.create_volunteer_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    # Unauthorized access should return 403 Forbidden
    def test_create_volunteer_preferences_unauthorized(self):
        self.client.logout()
        response = self.client.post(self.create_volunteer_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Sending invalid data should return 400 Bad Request
    def test_create_volunteer_preferences_invalid_data(self):
        data = {
            "availability": "invalid_format",  # Should be a list
            "preferred_work_types": "invalid_choice"  # Should be a valid choice
        }
        response = self.client.post(self.create_volunteer_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # Non-volunteer accounts should not be able to create preferences
    def test_non_volunteer_cannot_create_preferences(self):
        regular_account = Account.objects.create_user(
            email_address="regular@example.com",
            password="testpass",
            user_type="organization",
            contact_number="+35687654321"
        )
        self.client.force_authenticate(user=regular_account)
        response = self.client.post(self.create_volunteer_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Sending a GET request should return 405 Method Not Allowed
    def test_wrong_method_returns_405(self):
        response = self.client.get(self.create_volunteer_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Successfully create volunteer preferences with location
    def test_create_volunteer_preferences_with_location_success(self):
        data = {
            "availability": ["monday", "wednesday"],
            "preferred_work_types": "online",
            "preferred_duration": ["short-term"],
            "fields_of_interest": ["education", "community"],
            "skills": ["public speaking", "leadership"],
            "languages": ["English", "Spanish"],
            "location": {
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        }
        response = self.client.post(self.create_volunteer_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VolunteerMatchingPreferences.objects.count(), 1)
        self.assertEqual(response.data["data"]["volunteer"], self.volunteer.pk)
        self.assertEqual(response.data["data"]["location"]["city"], "New York")

    # Sending invalid location data should return 400 Bad Request
    def test_create_volunteer_preferences_invalid_location(self):
        data = {
            "location": "invalid_location_format"  # Should be a dict
        }
        response = self.client.post(self.create_volunteer_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Attempt to create duplicate preferences (should return 409 Conflict)
    def test_create_duplicate_volunteer_preferences_with_location(self):
        VolunteerMatchingPreferences.objects.create(volunteer=self.volunteer, location={})
        response = self.client.post(self.create_volunteer_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    # Test retrieving volunteer preferences (successful)
    def test_get_volunteer_preferences_success(self):
        VolunteerMatchingPreferences.objects.create(
            volunteer=self.volunteer,
            preferred_work_types="online",
            location={"city": "New York"}
        )
        response = self.client.get(self.get_volunteer_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['preferred_work_types'], "online")

    # Test retrieving preferences when they don't exist
    def test_get_volunteer_preferences_not_found(self):
        response = self.client.get(self.get_volunteer_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test non-volunteers cannot retrieve preferences
    def test_non_volunteer_cannot_get_preferences(self):
        org_account = Account.objects.create_user(email_address="org@example.com", password="testpass", user_type="organization", contact_number="+35612345679")
        self.client.force_authenticate(user=org_account)
        response = self.client.get(self.get_volunteer_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test updating volunteer preferences (successful)
    def test_update_volunteer_preferences_success(self):
        prefs = VolunteerMatchingPreferences.objects.create(
            volunteer=self.volunteer,
            preferred_work_types="online",
            location={"city": "New York"}
        )
        data = {
            "preferred_work_types": "in-person",
            "skills": ["coding", "leadership"]
        }
        response = self.client.patch(self.update_volunteer_preferences_url, data, format="json")
        prefs.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(prefs.preferred_work_types, "in-person")
        self.assertEqual(prefs.skills, ["coding", "leadership"])

    # Test updating preferences when they don't exist
    def test_update_volunteer_preferences_not_found(self):
        data = {
            "preferred_work_types": "in-person"
        }
        response = self.client.patch(self.update_volunteer_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test invalid data when updating preferences
    def test_update_volunteer_preferences_invalid_data(self):
        VolunteerMatchingPreferences.objects.create(volunteer=self.volunteer)
        data = {"skills": "invalid_json"}
        response = self.client.patch(self.update_volunteer_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class TestOrganizationPreferencesAPI(APITestCase):
    def setUp(self):
        self.organization_account = Account.objects.create_user(
            email_address="organization@example.com",
            password="testpass",
            user_type="organization",
            contact_number="+35612345678"
        )
        self.organization = Organization.objects.create(
            account=self.organization_account,
            organization_name="Helping Hands",
            organization_address="123 Volunteer St.",
            organization_website="https://helpinghands.org"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.organization_account)

        self.create_organization_preferences_url = reverse("volunteers_organizations:create_organization_preferences")
        self.get_organization_preferences_url = reverse("volunteers_organizations:get_organization_preferences")
        self.update_organization_preferences_url = reverse("volunteers_organizations:update_organization_preferences")

    # Successfully create organization preferences
    def test_create_organization_preferences_success(self):
        data = {
            "location": {
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        }
        response = self.client.post(self.create_organization_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrganizationPreferences.objects.count(), 1)
        self.assertEqual(response.data["data"]["organization"], self.organization.pk)

    # Attempt to create duplicate preferences (should return 409 Conflict)
    def test_create_duplicate_organization_preferences(self):
        OrganizationPreferences.objects.create(organization=self.organization)
        response = self.client.post(self.create_organization_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    # Unauthorized access should return 403 Forbidden
    def test_create_organization_preferences_unauthorized(self):
        self.client.logout()
        response = self.client.post(self.create_organization_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Sending invalid data should return 400 Bad Request
    def test_create_organization_preferences_invalid_data(self):
        data = {
            "location": "invalid_location_format"  # Should be a dict
        }
        response = self.client.post(self.create_organization_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Sending a GET request should return 405 Method Not Allowed
    def test_wrong_method_returns_405(self):
        response = self.client.get(self.create_organization_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Successfully create organization preferences with location
    def test_create_organization_preferences_with_location_success(self):
        data = {
            "location": {
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        }
        response = self.client.post(self.create_organization_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrganizationPreferences.objects.count(), 1)
        self.assertEqual(response.data["data"]["organization"], self.organization.pk)
        self.assertEqual(response.data["data"]["location"]["city"], "New York")

    # Sending invalid location data should return 400 Bad Request
    def test_create_organization_preferences_invalid_location(self):
        data = {
            "location": "invalid_location_format"  # Should be a dict
        }
        response = self.client.post(self.create_organization_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Attempt to create duplicate preferences (should return 409 Conflict)
    def test_create_duplicate_organization_preferences_with_location(self):
        OrganizationPreferences.objects.create(organization=self.organization, location={})
        response = self.client.post(self.create_organization_preferences_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    # Test retrieving organization preferences (successful)
    def test_get_organization_preferences_success(self):
        OrganizationPreferences.objects.create(
            organization=self.organization,
            location={
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        )
        response = self.client.get(self.get_organization_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Test retrieving preferences when they don't exist
    def test_get_organization_preferences_not_found(self):
        response = self.client.get(self.get_organization_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test non-organization users cannot retrieve preferences
    def test_non_organization_cannot_get_preferences(self):
        vol_account = Account.objects.create_user(email_address="vol@example.com", password="testpass", user_type="volunteer")
        self.client.force_authenticate(user=vol_account)
        response = self.client.get(self.get_organization_preferences_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test updating organization preferences (successful)
    def test_update_organization_preferences_success(self):
        prefs = OrganizationPreferences.objects.create(
            organization=self.organization,
            location={
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        )
        data = {"location": {
                "lat": 35.7128,
                "lon": 14.0060,
                "city": "St Julians",
                "formatted_address": "St Julians, Malta"
            }}
        response = self.client.patch(self.update_organization_preferences_url, data, format="json")
        prefs.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Test updating preferences when they don't exist
    def test_update_organization_preferences_not_found(self):
        data = {"location": {
                "lat": 35.7128,
                "lon": 14.0060,
                "city": "St Julians",
                "formatted_address": "St Julians, Malta"
            }}
        response = self.client.patch(self.update_organization_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test invalid data when updating preferences
    def test_update_organization_preferences_invalid_data(self):
        OrganizationPreferences.objects.create(organization=self.organization)
        data = {"location": "invalid_location"}
        response = self.client.patch(self.update_organization_preferences_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DonateVolonteraPointsTests(APITestCase):
    
    def setUp(self):
        # Create volunteer user
        self.volunteer_user = Account.objects.create_user(
            email_address="volunteer@test.com",
            password="password123",
            user_type="volunteer",
            contact_number="+123456789"
        )
        self.volunteer = Volunteer.objects.create(
            account=self.volunteer_user,
            first_name="John",
            last_name="Doe",
            dob="1990-01-01",
            volontera_points=100  # Give volunteer initial points
        )

        # Create organization user
        self.organization_user = Account.objects.create_user(
            email_address="org@test.com",
            password="password123",
            user_type="organization",
            contact_number="+987654321"
        )
        self.organization = Organization.objects.create(
            account=self.organization_user,
            organization_name="Helping Hands",
            organization_description="Non-profit organization.",
            organization_address={
                'raw': '123 Help St, Kindness City, US',
                'street_number': '123',
                'route': 'Help St',
                'locality': 'Kindness City',
                'postal_code': '12345',
                'state': 'CA',
                'state_code': 'CA',
                'country': 'United States',
                'country_code': 'US'
            },
            volontera_points=0  # Start with 0 points
        )

        # Authenticate the volunteer
        self.client.force_authenticate(user=self.volunteer_user)

        # API URL with organization UUID
        self.url = reverse("volunteers_organizations:donate_volontera_points", args=[self.organization_user.account_uuid])
    
    def test_valid_donation(self):
        data = {"amount": "50"}  # Donate 50 points
        response = self.client.post(self.url, data)

        self.volunteer.refresh_from_db()
        self.organization.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.volunteer.volontera_points, 50)  # 100 - 50 = 50
        self.assertEqual(self.organization.volontera_points, 50)  # 0 + 50 = 50
        self.assertIn("Successfully donated", response.data["message"])

    def test_donation_insufficient_points(self):
        data = {"amount": "200"}  # More than the volunteer has
        response = self.client.post(self.url, data)

        self.volunteer.refresh_from_db()
        self.organization.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.volunteer.volontera_points, 100)  # No change
        self.assertEqual(self.organization.volontera_points, 0)  # No change
        self.assertIn("Not enough points", response.data["error"])

    def test_donation_invalid_amount(self):
        data = {"amount": "-10"}  # Negative points
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Donation amount must be greater than zero", response.data["error"])

    def test_donation_non_numeric_amount(self):
        data = {"amount": "abc"}  # Non-numeric input
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid amount", response.data["error"])

    def test_donation_nonexistent_organization(self):
        fake_uuid = "11111111-2222-3333-4444-555555555555"
        url = reverse("volunteers_organizations:donate_volontera_points", kwargs={"organization_id": fake_uuid})
        
        data = {"amount": "20"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Organization not found", response.data["error"])

    def test_donation_unauthorized(self):
        self.client.logout()  # Simulate an unauthenticated request
        data = {"amount": "30"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)