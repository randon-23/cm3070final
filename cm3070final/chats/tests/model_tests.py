from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from accounts_notifs.models import Account
from ..models import Chat, Message
import datetime

def create_common_objects():
    # Set up two participants
    participant_1 = Account.objects.create(
        email_address="user1@test.com",
        password="password",
        user_type="volunteer",
        contact_number="+35612345678"
    )
    participant_2 = Account.objects.create(
        email_address="user2@test.com",
        password="password",
        user_type="volunteer",
        contact_number="+35612345679"
    )
    return participant_1, participant_2

class TestChatModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1, cls.user2 = create_common_objects()
    
    def test_chat_creation(self):
        chat=Chat.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        self.assertEqual(chat.participant_1, self.user1)
        self.assertEqual(chat.participant_2, self.user2)

    def test_unique_chat_between_participants(self):
        Chat.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        # Second chat should not be created between the same participants
        with self.assertRaises(IntegrityError):
            Chat.objects.create(
                participant_1=self.user1,
                participant_2=self.user2
            )
    
    def test_reverse_order_chat(self):
        Chat.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        # Second chat should not be created, even if the order of participants is reversed
        with self.assertRaises(ValidationError):
            Chat.objects.create(
                participant_1=self.user2,
                participant_2=self.user1
            )

class TestMessageModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1, cls.user2 = create_common_objects()
        cls.chat = Chat.objects.create(
            participant_1=cls.user1,
            participant_2=cls.user2
        )
    
    def test_message_creation_user1(self):
        message = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="Hello test message"
        )
        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Hello test message")
        self.assertIsInstance(message.timestamp, datetime.datetime)
        self.assertFalse(message.is_read)

    def test_message_creation_user2(self):
        message = Message.objects.create(
            chat=self.chat,
            sender=self.user2,
            content="Hello test message"
        )
        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.sender, self.user2)
        self.assertEqual(message.content, "Hello test message")
        self.assertIsInstance(message.timestamp, datetime.datetime)
        self.assertFalse(message.is_read)
    
    def test_message_ordering(self):
        message1 = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="Hello test message 1"
        )
        message2 = Message.objects.create(
            chat=self.chat,
            sender=self.user2,
            content="Hello test message 2"
        )
        messages = Message.objects.all()
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)

    def test_external_user_not_allowed(self):
        external_user = Account.objects.create(
            email_address="testuser3@test.com",
            password="password",
            user_type="volunteer"
        )

        with self.assertRaises(ValidationError):
            Message.objects.create(
                chat=self.chat,
                sender=external_user,
                content="Hello test message"
            )


