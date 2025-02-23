from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Volunteer, Organization, Following, Endorsement, StatusPost
from ..serializers import VolunteerSerializer, OrganizationSerializer, FollowingCreateSerializer
from accounts_notifs.models import Account
from accounts_notifs.serializers import AccountSerializer
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
