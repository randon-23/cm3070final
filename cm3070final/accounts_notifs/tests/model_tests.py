from django.test import TestCase
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from ..models import Account, AccountPreferences, Notification
from uuid import UUID

def create_common_objects():
    #Creating a volunteer account
    volunteer = Account.objects.create(
        email_address='test_email_vol@tester.com',
        password='testerpassword',
        user_type='volunteer',
        contact_number="+35612345678"
    )
    organization = Account.objects.create(
        email_address='test_email_org@tester.com',
        password='testerpassword',
        user_type='organization',
        contact_number="+35612345679"
    )
    admin = Account.objects.create(
        email_address='test_email_org_admin@tester.com',
        password='testerpassword',
        user_type='admin',
        contact_number="+35612345670"
    )
    return volunteer, organization, admin

# Test for Account model
class TestAccountModel(TestCase):
    #Setting up groups and accounts
    @classmethod
    def setUpTestData(cls):
        cls.volunteer, cls.organization, cls.admin = create_common_objects()
    
    # Test for creating a volunteer account
    def test_create_volunteer_account(self):
        self.assertEqual(self.volunteer.email_address, 'test_email_vol@tester.com')
        self.assertEqual(self.volunteer.password, 'testerpassword')
        self.assertTrue(self.volunteer.is_volunteer())
        self.assertFalse(self.volunteer.is_organization())
        self.assertFalse(self.organization.is_admin())
        self.assertIsInstance(self.volunteer.account_uuid, UUID)
    
    def test_create_organization_account(self):
        self.assertEqual(self.organization.email_address, 'test_email_org@tester.com'),
        self.assertEqual(self.organization.password, 'testerpassword')
        self.assertTrue(self.organization.is_organization())
        self.assertFalse(self.organization.is_volunteer())
        self.assertFalse(self.organization.is_admin())
        self.assertIsInstance(self.organization.account_uuid, UUID)

    def test_superuser_creation(self):
        self.assertEqual(self.admin.email_address, 'test_email_org_admin@tester.com'),
        self.assertEqual(self.admin.password, 'testerpassword'),
        self.assertFalse(self.admin.is_volunteer()),
        self.assertFalse(self.admin.is_organization()),
        self.assertIsInstance(self.admin.account_uuid, UUID)

    def test_user_groups(self):
        self.assertEqual(Group.objects.count(), 3)
        self.assertEqual(Group.objects.get(name='Volunteer').user_set.count(), 1)
        self.assertEqual(Group.objects.get(name='Organization').user_set.count(), 1)
        self.assertEqual(Group.objects.get(name='Admin').user_set.count(), 1)

    def test_unique_email_address(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Account.objects.create(
                    email_address='test_email_vol@tester.com',
                    password='testerpassword',
                    user_type='volunteer'
                )

class TestAccountPreferencesModel(TestCase):
    #Setting up groups and accounts
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, cls.organization_account, _ = create_common_objects()
    
    def test_volunteer_preferences(self):
        preferences = AccountPreferences.objects.create(account=self.volunteer_account)
        preferences.save()

        self.assertIsNone(preferences.enable_volontera_point_opportunities)
        self.assertIsNone(preferences.volontera_points_rate)
        self.assertTrue(preferences.smart_matching_enabled)

    def test_organization_preferences(self):
        preferences = AccountPreferences.objects.create(account=self.organization_account)
        preferences.save()

        self.assertFalse(preferences.smart_matching_enabled)
        self.assertIsNone(preferences.smart_matching_enabled)
        self.assertEqual(preferences.volontera_points_rate, 1.0)


class TestNotificationModel(TestCase):
    #Setting up groups and accounts
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, _, _ = create_common_objects()
    
    def test_valid_notification_creation(self):
        notification = Notification.objects.create(
            recipient=self.volunteer_account,
            notification_type="application",
            notification_message="Your application has been approved."
        )

        self.assertEqual(notification.notification_type, "application")
        self.assertEqual(notification.notification_message, "Your application has been approved.")
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.recipient, self.volunteer_account)

    def test_invalid_notification_type(self):
        notification = Notification(
            recipient=self.volunteer_account,
            notification_type="invalid_type",
            notification_message="This should fail."
        )
        with self.assertRaises(ValidationError):
            notification.full_clean()

    def test_notification_str_representation(self):
        """Test the string representation of the notification."""
        notification = Notification.objects.create(
            recipient=self.volunteer_account,
            notification_type="message",
            notification_message="You have a new message."
        )

        expected_str = f"{self.volunteer_account.email_address} - message - {notification.created_at}"
        self.assertEqual(str(notification), expected_str) 