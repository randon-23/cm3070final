from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Volunteer, Organization, Following
from ..serializers import VolunteerSerializer, OrganizationSerializer, FollowingCreateSerializer
from accounts_notifs.models import Account
from accounts_notifs.serializers import AccountSerializer
from django.urls import reverse

Account = get_user_model()

class TestFollowUnfollowAPITestCase(APITestCase):
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