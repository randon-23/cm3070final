from django.test import TestCase
from django.contrib.auth import get_user_model
from volunteers_organizations.models import Following, Endorsement, StatusPost
from volunteers_organizations.models import Volunteer, Organization
from unittest.mock import patch
from datetime import date
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

Account = get_user_model()

def create_common_objects():
    # Create common accounts
    volunteer_account_1 = Account.objects.create(
        email_address='follower@test.com',
        password='testerpassword',
        user_type='volunteer',
        contact_number="+35612345677"
    )

    volunteer_account_2 = Account.objects.create(
        email_address='test_email_vol@tester.com',
        password='testerpassword',
        user_type='volunteer',
        contact_number="+35612345678"
    )

    organization_account = Account.objects.create(
        email_address='test_email_org@tester.com',
        password='testerpassword',
        user_type='organization',
        contact_number="+35612345679"
    )

    return volunteer_account_1, volunteer_account_2, organization_account


class FollowingSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up class-level test data (executed once for the test class)
        cls.follower_account, cls.followed_volunteer_account, cls.followed_organization_account = create_common_objects()

        cls.follower_volunteer = Volunteer.objects.create(
            account=cls.follower_account,
            first_name="Jane",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )
        # Create volunteer & organization profiles
        cls.followed_volunteer = Volunteer.objects.create(
            account=cls.followed_volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        cls.followed_organization = Organization.objects.create(
            account=cls.followed_organization_account,
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
            }
        )
        cls.additional_organization_account = Account.objects.create(
            email_address='test_email_org1@tester.com',
            password='testerpassword',
            user_type='organization',
            contact_number="+35612345676"
        )
        cls.additional_organization_profile = Organization.objects.create(
            account=cls.additional_organization_account,
            organization_name="Helping Hands 2",
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
            }
        )

    def setUp(self):
        # Set up per-test dependencies
        self.client = APIClient()
        self.client.force_authenticate(user=self.follower_account)

    # Test that following a volunteer via API triggers notification.
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_following_volunteer_triggers_notification(self, mock_task):
        url = reverse("volunteers_organizations:create_following", args=[self.followed_volunteer.account.account_uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Following.objects.filter(follower=self.follower_account, followed_volunteer=self.followed_volunteer).exists())

        # Ensure Celery task was triggered with correct parameters
        mock_task.assert_called_once_with(
            recipient_id=str(self.followed_volunteer.account.account_uuid),
            notification_type="new_follower",
            message="Jane Doe started following you."
        )

    # Test that following an organization via API triggers notification.
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_following_organization_triggers_notification(self, mock_task):
        url = reverse("volunteers_organizations:create_following", args=[self.followed_organization.account.account_uuid])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Following.objects.filter(follower=self.follower_account, followed_organization=self.followed_organization).exists())

        # Ensure Celery task was triggered with correct parameters
        mock_task.assert_called_once_with(
            recipient_id=str(self.followed_organization.account.account_uuid),
            notification_type="new_follower",
            message="Jane Doe started following you."
        )

    # Ensure organizations cannot follow volunteers or other organizations.
    def test_organization_cannot_follow_other_organizations(self):
        url = reverse("volunteers_organizations:create_following", args=[self.additional_organization_profile.account.account_uuid])
        self.client.force_authenticate(user=self.followed_organization_account)

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Following.objects.filter(follower=self.followed_organization_account).exists())

class EndorsementSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up class-level test data (executed once for the test class)
        cls.volunteer_account_1, cls.volunteer_account_2, cls.organization_account = create_common_objects()

        cls.volunteer_1 = Volunteer.objects.create(
            account=cls.volunteer_account_1,
            first_name="Jane",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )
        # Create volunteer & organization profiles
        cls.volunteer_2 = Volunteer.objects.create(
            account=cls.volunteer_account_2,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
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
            }
        )
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.volunteer_account_1)

    # Test that an endorsement triggers the notification task
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_endorsement_triggers_notification(self, mock_task):
        Endorsement.objects.create(
            giver=self.volunteer_account_1,
            receiver=self.volunteer_account_2,
            endorsement="Great teamwork skills!"
        )

        # Ensure Celery task was triggered
        mock_task.assert_called_once_with(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="new_endorsement",
            message="You have received a new endorsement from Jane Doe!"
        )

    # Test the API actually triggers the notification
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_api_trigger_endorsement_notification(self, mock_task):
        url = reverse("volunteers_organizations:create_endorsement", args=[self.volunteer_account_2.account_uuid])
        self.client.force_authenticate(user=self.volunteer_account_1)

        response = self.client.post(url, {"endorsement": "Excellent communication skills!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Endorsement.objects.filter(giver=self.volunteer_account_1, receiver=self.volunteer_account_2).exists())

        # Ensure Celery task was triggered with correct parameters
        mock_task.assert_called_once_with(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="new_endorsement",
            message="You have received a new endorsement from Jane Doe!"
        )

    # Test that organization creating endorsement triggers notification
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_organization_endorsement_triggers_notification(self, mock_task):
        url = reverse("volunteers_organizations:create_endorsement", args=[self.volunteer_account_2.account_uuid])
        self.client.force_authenticate(user=self.organization_account)

        response = self.client.post(url, {"endorsement": "Well done on the job!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Endorsement.objects.filter(giver=self.organization_account, receiver=self.volunteer_account_2).exists())

        # Ensure Celery task was triggered with correct parameters
        mock_task.assert_called_once_with(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="new_endorsement",
            message="You have received a new endorsement from Helping Hands!"
        )

class StatusPostSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create base accounts
        cls.volunteer_account_1, cls.volunteer_account_2, cls.organization_account = create_common_objects()

        # Extra volunteer accounts for testing (one follows, one doesn't)
        cls.volunteer_account_3 = Account.objects.create(
            email_address='volunteer3@test.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345674"
        )

        cls.volunteer_account_4 = Account.objects.create(
            email_address='volunteer4@test.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345675"
        )

        # Create volunteer profiles
        cls.volunteer_1 = Volunteer.objects.create(
            account=cls.volunteer_account_1,
            first_name="Alice",
            last_name="Smith",
            dob=date(1996, 2, 2)
        )

        cls.volunteer_2 = Volunteer.objects.create(
            account=cls.volunteer_account_2,
            first_name="Bob",
            last_name="Johnson",
            dob=date(1997, 3, 3)
        )

        cls.volunteer_3 = Volunteer.objects.create(
            account=cls.volunteer_account_3,
            first_name="Charlie",
            last_name="Brown",
            dob=date(1998, 4, 4)
        )

        cls.volunteer_4 = Volunteer.objects.create(
            account=cls.volunteer_account_4,
            first_name="David",
            last_name="Wilson",
            dob=date(1999, 5, 5)
        )

        # Create an organization
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="A non-profit organization.",
            organization_address={
                'raw': '456 Charity Rd, Kindness City, US',
                'street_number': '456',
                'route': 'Charity Rd',
                'locality': 'Kindness City',
                'postal_code': '67890',
                'state': 'NY',
                'state_code': 'NY',
                'country': 'United States',
                'country_code': 'US'
            }
        )

        # Volunteer 2 & 3 follow Volunteer 1
        Following.objects.create(follower=cls.volunteer_account_2, followed_volunteer=cls.volunteer_1)
        Following.objects.create(follower=cls.volunteer_account_3, followed_volunteer=cls.volunteer_1)

        # Volunteer 4 does NOT follow Volunteer 1
        # (so we can test that they don't receive a notification)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.volunteer_account_1)

    # Test that posting a status via API triggers the notification for followers
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_status_post_triggers_notifications(self, mock_task):
        url = reverse("volunteers_organizations:create_status_post")
        response = self.client.post(url, {"content": "Excited to volunteer!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ensure Celery task was triggered twice (only for the two followers)
        self.assertEqual(mock_task.call_count, 2)

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="new_status_post",
            message="Alice Smith has posted a new status update!"
        )

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_3.account_uuid),
            notification_type="new_status_post",
            message="Alice Smith has posted a new status update!"
        )

    # Test that a status post does NOT notify non-followers
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_non_followers_do_not_get_notification(self, mock_task):
        url = reverse("volunteers_organizations:create_status_post")
        response = self.client.post(url, {"content": "Another great day volunteering!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Volunteer 4 is not following, should NOT be notified
        unexpected_call = (
            str(self.volunteer_account_4.account_uuid),
            "new_status_post",
            "Alice Smith has posted a new status update!"
        )

        # Ensure the notification was NOT sent to the non-follower
        for call_args in mock_task.call_args_list:
            self.assertNotEqual(call_args[0], unexpected_call)

    # Test that an organization posting via API triggers notifications
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_organization_status_post_triggers_notifications(self, mock_task):
        # Authenticate as the organization
        self.client.force_authenticate(user=self.organization_account)

        url = reverse("volunteers_organizations:create_status_post")
        response = self.client.post(url, {"content": "We need more volunteers!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ensure no errors occur (we don't expect followers yet)
        self.assertEqual(mock_task.call_count, 0)

    # Test that organization posting notifies followers
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_organization_status_post_notifies_followers(self, mock_task):
        # Create followers for the organization
        Following.objects.create(follower=self.volunteer_account_1, followed_organization=self.organization)
        Following.objects.create(follower=self.volunteer_account_2, followed_organization=self.organization)

        self.assertEqual(Following.objects.filter(followed_organization=self.organization).count(), 2)

        # Clear previous call history from Following creation signals
        mock_task.reset_mock()

        # Authenticate as the organization
        self.client.force_authenticate(user=self.organization_account)

        url = reverse("volunteers_organizations:create_status_post")
        response = self.client.post(url, {"content": "We need more volunteers!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ensure Celery task was triggered twice (only for the two followers)
        self.assertEqual(mock_task.call_count, 2)

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_1.account_uuid),
            notification_type="new_status_post",
            message="Helping Hands has posted a new status update!"
        )

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="new_status_post",
            message="Helping Hands has posted a new status update!"
        )

class DonationSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account = Account.objects.create_user(
            email_address="volunteer@test.com",
            password="password123",
            user_type="volunteer",
            contact_number="+37112345678"
        )
        cls.volunteer = Volunteer.objects.create(account=cls.volunteer_account, first_name='John', last_name='Doe', dob=date(1990, 3, 3), volontera_points=50)

        cls.organization_account = Account.objects.create_user(
            email_address="org@test.com",
            password="password123",
            user_type="organization",
            contact_number="+37187654321"
        )
        cls.organization = Organization.objects.create(account=cls.organization_account, organization_name="Helping Hands", organization_description="Non-profit organization.", volontera_points=0)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.volunteer_account)

    # Test that donating Volontera points sends a notification to the organization
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_donate_volontera_points_triggers_notification(self, mock_notification_task):
        url = reverse("volunteers_organizations:donate_volontera_points", args=[self.organization.account.account_uuid])

        response = self.client.post(url, {"amount": 20})

        # Check if API returned success
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify notification was triggered
        mock_notification_task.assert_called_once_with(
            recipient_id=str(self.organization_account.account_uuid),
            notification_type="new_volontera_points",
            message=f"Your organization has received a donation of 20.0 Volontera points!"
        )

        # Check if Volontera points updated correctly
        self.volunteer.refresh_from_db()
        self.organization.refresh_from_db()
        self.assertEqual(self.volunteer.volontera_points, 30)  # 50 - 20
        self.assertEqual(self.organization.volontera_points, 20)  # +20 received