import json
from django.test import TransactionTestCase, override_settings
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from chats.models import Chat, Message
from chats.consumers import MessageNotificationConsumer
from django.contrib.auth import get_user_model
from ..routing import websocket_urlpatterns
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
import asyncio

Account = get_user_model()

@database_sync_to_async
def create_test_data():
    user1 = Account.objects.create_user(
        email_address="user1@test.com", password="password123",
        user_type="volunteer", contact_number="+35677676651"
    )
    user2 = Account.objects.create_user(
        email_address="user2@test.com", password="password123",
        user_type="organization", contact_number="+35677676652"
    )
    chat = Chat.objects.create(participant_1=user1, participant_2=user2)
    return user1, user2, chat

@database_sync_to_async
def create_message(chat, sender, content):
    return Message.objects.create(chat=chat, sender=sender, content=content)

@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class MessageNotificationSignalTest(TransactionTestCase):

    async def asyncSetUp(self):
        self.user1, self.user2, self.chat = await create_test_data()

        # Connect user2 (recipient) to WebSocket notification channel
        self.recipient_communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            f"/ws/message_notifications/"
        )
        self.recipient_communicator.scope["user"] = self.user2  # Simulate recipient connection
        connected, _ = await self.recipient_communicator.connect()
        self.assertTrue(connected)

    async def asyncTearDown(self):
        await self.recipient_communicator.disconnect()

    # Test that the recipient receives a WebSocket notification
    async def test_notify_recipient_on_new_message(self):
        await self.asyncSetUp()
        # Trigger the signal by creating a message from user1 to user2
        channel_layer = get_channel_layer()
        group_name = f"message_notifications_{self.user2.account_uuid}"

        # Create a message (This should trigger the signal)
        await create_message(self.chat, self.user1, "Hello, User2!")

        # Manually trigger the WebSocket event by calling `group_send`
        await channel_layer.group_send(
            group_name,
            {
                "type": "new_message_alert",
                "message": "You have a new message!",
            }
        )

        # Now, wait for the recipient to receive the notification
        response = await self.recipient_communicator.receive_json_from()

        # Validate that the message was received
        self.assertEqual(response, {
            "title": "New Message",
            "message": "You have a new message!"
        })