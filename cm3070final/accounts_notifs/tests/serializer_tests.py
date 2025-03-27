import uuid
from django.test import TestCase
from ..models import Account, Notification
from ..serializers import AccountSerializer, NotificationSerializer
from django.contrib.auth import get_user_model

Account = get_user_model()

class TestAccountSerializer(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email_address="testuser@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+35612345678"
        )

    # Test if the serializer correctly serializes an Account instance
    def test_serialization(self):
        serializer = AccountSerializer(instance=self.account)
        data = serializer.data

        self.assertEqual(data["account_uuid"], str(self.account.account_uuid))
        self.assertEqual(data["email_address"], self.account.email_address)
        self.assertEqual(data["contact_number"], self.account.contact_number)
        self.assertEqual(data["user_type"], self.account.user_type)
        self.assertIn("created_at", data)  # Ensures created_at is included

    # Test if the serializer correctly validates and deserializes valid data
    def test_deserialization_valid_data(self):
        valid_data = {
            "email_address": "newuser@example.com",
            "contact_number": "+35698765432",
            "user_type": "organization",
        }

        serializer = AccountSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # Test if the serializer correctly handles missing fields
    def test_deserialization_missing_fields(self):
        invalid_data = {
            "email_address": "missingfields@example.com",
        }

        serializer = AccountSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("contact_number", serializer.errors)
        self.assertIn("user_type", serializer.errors)

    # Test if the serializer rejects invalid email formats
    def test_invalid_email_format(self):
        invalid_data = {
            "email_address": "invalid-email",
            "contact_number": "+35698765432",
            "user_type": "volunteer",
        }

        serializer = AccountSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email_address", serializer.errors)

    # Test if the serializer rejects an invalid user_type
    def test_invalid_user_type(self):
        invalid_data = {
            "email_address": "valid@example.com",
            "contact_number": "+35698765432",
            "user_type": "invalid_type",
        }

        serializer = AccountSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_type", serializer.errors)

class TestNotificationSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account = Account.objects.create_user(email_address="testuser@example.com", password="testpassword", user_type="volunteer", contact_number="+35612345678")
        cls.notification = Notification.objects.create(
            recipient=cls.volunteer_account,
            notification_type="other",
            notification_message="Test notification message"
        )
    
    def test_serialization(self):
        serializer = NotificationSerializer(instance=self.notification)
        data = serializer.data

        self.assertTrue(uuid.UUID(data["notification_uuid"]))
        self.assertEqual(data["recipient"], self.notification.recipient.account_uuid)
        self.assertEqual(data["notification_type"], self.notification.notification_type)
        self.assertEqual(data["notification_message"], self.notification.notification_message)

    def test_empty_serializer(self):
        serializer = NotificationSerializer(data={})
        self.assertFalse(serializer.is_valid())