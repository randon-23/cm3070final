from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from ..models import Account, Notification

Account = get_user_model()

class AuthenticationAPITestCase(APITestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            email_address="testuser@example.com",
            password="SecurePassword123!",
            user_type="volunteer",
            contact_number="+35612345678"
        )
        self.login_url = reverse('accounts_notifs:login')
        self.logout_url = reverse('accounts_notifs:logout')
        self.password_reset_request_url = reverse('accounts_notifs:password_reset_request')
        self.password_reset_confirm_url = reverse('accounts_notifs:password_reset_confirm')

    # Test successful login
    def test_login_success(self):
        response = self.client.post(self.login_url, {'email': 'testuser@example.com', 'password': 'SecurePassword123!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Login successful!')

    # Test login failure with incorrect credentials
    def test_login_failure_invalid_credentials(self):
        response = self.client.post(self.login_url, {'email': 'testuser@example.com', 'password': 'WrongPassword'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    # Test logout endpoint
    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logout successful!')

    # Test password reset request with a valid email
    def test_password_reset_request_success(self):
        response = self.client.post(self.password_reset_request_url, {'email': 'testuser@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Password reset link sent to your email')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Request', mail.outbox[0].subject)

    # Test password reset request with an invalid email
    def test_password_reset_request_invalid_email(self):
        response = self.client.post(self.password_reset_request_url, {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    # Test successful password reset
    def test_password_reset_confirm_success(self):
        token = default_token_generator.make_token(self.user)
        data = {
            'user': str(self.user.account_uuid),
            'token': token,
            'new_password': 'NewSecurePassword123!',
            'confirm_password': 'NewSecurePassword123!'
        }
        response = self.client.post(self.password_reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Password reset successful')

        # Ensure new password is set
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePassword123!'))

    # Test password reset failure due to invalid token
    def test_password_reset_confirm_invalid_token(self):
        data = {
            'user': str(self.user.account_uuid),
            'token': 'invalid_token',
            'new_password': 'NewSecurePassword123!',
            'confirm_password': 'NewSecurePassword123!'
        }
        response = self.client.post(self.password_reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    # Test password reset failure due to mismatched passwords
    def test_password_reset_confirm_mismatched_passwords(self):
        token = default_token_generator.make_token(self.user)
        data = {
            'user': str(self.user.account_uuid),
            'token': token,
            'new_password': 'NewSecurePassword123!',
            'confirm_password': 'MismatchPassword!'
        }
        response = self.client.post(self.password_reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

class NotificationAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        cls.volunteer_account = Account.objects.create(
            email_address='test_email_vol@tester.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345678"
        )
        cls.organization_account = Account.objects.create(
            email_address="test_email_org@tester.com",
            password="testerpassword",
            user_type="organization",
            contact_number="+35612345672"
        )

        cls.notification = Notification.objects.create(
            recipient=cls.volunteer_account,
            notification_type="application_accepted",
            notification_message="Your application for 'Community Cleanup' has been accepted!",
            is_read=False,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)

    # Test retrieving unread notifications for authenticated user.
    def test_get_notifications_success(self):
        url = reverse("accounts_notifs:get_notifications", args=[str(self.volunteer_account.account_uuid)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only 1 unread notification
        self.assertEqual(response.data[0]["notification_type"], "application_accepted")

    # Test unauthorized access to another user's notifications.
    def test_get_notifications_unauthorized(self):
        url = reverse("accounts_notifs:get_notifications", args=[str(self.organization_account.account_uuid)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Unauthorized request")

    # Test marking a notification as read.
    def test_mark_notification_as_read_success(self):
        url = reverse("accounts_notifs:mark_read", args=[str(self.notification.notification_uuid)])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    # Test unauthorized attempt to mark someone else's notification as read.
    def test_mark_notification_as_read_unauthorized(self):
        self.client.force_authenticate(user=self.organization_account)
        url = reverse("accounts_notifs:mark_read", args=[str(self.notification.notification_uuid)])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Unauthorized request")