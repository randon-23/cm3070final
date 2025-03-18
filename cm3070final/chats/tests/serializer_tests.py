from django.test import TestCase
from accounts_notifs.models import Account
from chats.models import Chat, Message
from volunteers_organizations.models import Volunteer, Organization
from chats.serializers import ChatSerializer, MessageSerializer
from datetime import timezone

class ChatSerializerTest(TestCase):
    def setUp(self):
        # Create two test users
        self.user1 = Account.objects.create_user(email_address="user1@test.com", password="password123", user_type="volunteer", contact_number="+37112345678")
        self.user2 = Account.objects.create_user(email_address="user2@test.com", password="password123", user_type="organization", contact_number="+37187654321")

        self.volunteer = Volunteer.objects.create(
            account=self.user1,
            first_name="John",
            last_name="Doe",
            dob="1990-01-01",
        )
        self.organization=Organization.objects.create(
            account=self.user2,
            organization_name="Save the Earth",
            organization_description="An organization dedicated to environmental conservation",
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
        # Create a chat between the two users
        self.chat = Chat.objects.create(participant_1=self.user1, participant_2=self.user2)

        self.message = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="Hello, this is a test message!"
        )

    def test_chat_serializer(self):
        serializer = ChatSerializer(instance=self.chat)
        expected_data = {
            "chat_id": str(self.chat.chat_id),
            'participant_1': {'account_uuid': str(self.user1.account_uuid), 'email_address': 'user1@test.com', 'user_type': 'Volunteer', 'volunteer': {'first_name': 'John', 'last_name': 'Doe', 'dob': '1990-01-01', 'bio': '', 'profile_img': None, 'followers': 0, 'profile_url': f'/volunteers-organizations/profile/{str(self.user1.account_uuid)}'}, 'organization': None}, 
            'participant_2': {'account_uuid': str(self.user2.account_uuid), 'email_address': 'user2@test.com', 'user_type': 'Organization', 'volunteer': None, 'organization': {'organization_name': 'Save the Earth', 'organization_description': 'An organization dedicated to environmental conservation', 'organization_address': {'raw': '123 Greenway Blvd, Springfield, US', 'street_number': '123', 'route': 'Greenway Blvd', 'locality': 'Springfield', 'postal_code': '12345', 'state': 'Illinois', 'state_code': 'IL', 'country': 'United States', 'country_code': 'US'}, 'organization_website': None, 'organization_profile_img': None, 'followers': 0, 'profile_url': f'/volunteers-organizations/profile/{str(self.user2.account_uuid)}'}},
            "last_updated_at": self.chat.last_updated_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "last_message": "Hello, this is a test message!"
        }
        self.assertEqual(serializer.data, expected_data)


class MessageSerializerTest(TestCase):
    def setUp(self):
        # Create users and chat
        self.user1 = Account.objects.create_user(email_address="user1@test.com", password="password123", user_type="volunteer", contact_number="+37112345678")
        self.user2 = Account.objects.create_user(email_address="user2@test.com", password="password123", user_type="volunteer", contact_number="+37187654321")
        self.chat = Chat.objects.create(participant_1=self.user1, participant_2=self.user2)

        # Create a message
        self.message = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="Hello, this is a test message!"
        )

    def test_message_serializer(self):
        serializer = MessageSerializer(instance=self.message)
        expected_data = {
            "message_id": str(self.message.message_id),
            "chat": self.chat.chat_id,
            "sender": self.user1.account_uuid,
            "content": "Hello, this is a test message!",
            "timestamp": self.message.timestamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "is_read": False,
        }
        self.assertEqual(serializer.data, expected_data)

    def test_message_validation_valid(self):
        valid_message_data = {
            "chat": self.chat.chat_id,
            "sender": self.user1.account_uuid,
            "content": "This is a valid message!"
        }
        serializer = MessageSerializer(data=valid_message_data)
        self.assertTrue(serializer.is_valid())

    def test_message_validation_sender_not_in_chat(self):
        # Create a third user not in the chat
        outsider = Account.objects.create_user(email_address="outsider@test.com", password="password123", user_type="volunteer", contact_number="+37112345679")

        # Attempt to create a message with an invalid sender
        invalid_message_data = {
            "chat": self.chat.chat_id,
            "sender": outsider.account_uuid,  # Not a participant
            "content": "I should not be able to send this message!"
        }
        serializer = MessageSerializer(data=invalid_message_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("Sender must be a participant in the chat", serializer.errors["non_field_errors"][0])