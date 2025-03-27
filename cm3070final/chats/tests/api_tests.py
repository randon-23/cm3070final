from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from accounts_notifs.models import Account
from chats.models import Chat, Message
from volunteers_organizations.models import Volunteer, Organization
import uuid

class ChatMessageAPITestCase(APITestCase):
    def setUp(self):
        # Create two users
        self.user1 = Account.objects.create_user(email_address="user1@test.com", password="password123", user_type="volunteer", contact_number="+3522194828")
        self.user2 = Account.objects.create_user(email_address="user2@test.com", password="password123", user_type="organization", contact_number="+3522134828")

        self.volunteer = Volunteer.objects.create(
            account=self.user1,
            first_name="John",
            last_name="Doe", 
            dob="1995-06-15" 
        )

        self.organization = Organization.objects.create(
            account=self.user2,
            organization_name="Helping Hands",
            organization_address="123 Volunteer St.",
            organization_website="https://helpinghands.org"
        )
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Create a chat
        self.chat = Chat.objects.create(participant_1=self.user1, participant_2=self.user2)

        # Create a message
        self.message = Message.objects.create(
            chat=self.chat, sender=self.user1, content="Hello, this is a test message!"
        )

    # Test retrieving all chats for the authenticated user
    def test_get_chats(self):
        url = reverse("chats:get_chats")  # Assuming name in urls.py is 'get_chats'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["chat_id"], str(self.chat.chat_id))

    # Test retrieving messages for a chat
    def test_get_messages_for_chat(self):
        url = reverse("chats:get_messages", args=[str(self.chat.chat_id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "Hello, this is a test message!")

    # Test sending a message to an existing chat
    def test_send_message_existing_chat(self):
        url = reverse("chats:send_message", args=[str(self.chat.chat_id)])
        data = {
            "chat_id": str(self.chat.chat_id),
            "content": "This is another test message!"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 2)
        self.assertEqual(Message.objects.last().content, "This is another test message!")

    # Test sending a message when the chat does not exist (should fail)
    def test_send_message_chat_does_not_exist(self):
        url = reverse("chats:send_message", args=[str(uuid.uuid4())])  # Random UUID (chat does not exist)
        data = {
            "chat_id": str(uuid.uuid4()),  # Random UUID (chat does not exist)
            "content": "This should fail!"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test starting a new chat if one does not exist
    def test_start_or_send_message_creates_chat(self):
        url = reverse("chats:start_or_send_message")
        data = {
            "recipient_id": str(self.user2.account_uuid),
            "content": "Hello, let's start a chat!"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.count(), 1)  # Chat should still be unique
        self.assertEqual(Message.objects.count(), 2)  # Two messages in total now

    # Test marking a message as read
    def test_mark_message_as_read(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse("chats:mark_messages_read", args=[str(self.chat.chat_id)])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)

    # Ensure users cannot mark others' messages as read
    def test_mark_message_as_read_unauthorized(self):
        other_user = Account.objects.create_user(email_address="test@tester.biz", password="password123", user_type="volunteer", contact_number="+3522194808")
        self.client.force_authenticate(user=other_user)

        url = reverse("chats:mark_messages_read", args=[str(self.chat.chat_id)])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)