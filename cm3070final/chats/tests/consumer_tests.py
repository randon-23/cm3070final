import json
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings
from channels.layers import get_channel_layer
from chats.models import Chat, Message
from chats.consumers import MessageNotificationConsumer
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from ..routing import websocket_urlpatterns

Account = get_user_model()

@database_sync_to_async
def create_test_data():
    user1 = Account.objects.create_user(email_address="test@tester.com", password="password123", user_type="volunteer", contact_number="+35677676652")
    user2 = Account.objects.create_user(email_address="tester@test.com", password="password123", user_type="organization", contact_number="+35677676653")
    chat = Chat.objects.create(participant_1=user1, participant_2=user2)
    return user1, user2, chat

@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class MessageNotificationConsumerTest(TransactionTestCase):
    async def asyncSetUp(self):
        self.user1, self.user2, self.chat = await create_test_data()

        self.communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            f"/ws/message_notifications/"
        )
        self.communicator.scope["user"] = self.user2  # Simulate user2 connection
        connected, _ = await self.communicator.connect()
        self.assertTrue(connected)

    async def asyncTearDown(self):
        await self.communicator.disconnect()

    # Ensure user receives a new message alert when messaged.
    async def test_receive_new_message_alert(self):
        await self.asyncSetUp()
        group_name = f"message_notifications_{self.user2.account_uuid}"

        channel_layer = get_channel_layer()
        # Simulate message being sent (triggers signal)
        await channel_layer.group_send(
            group_name,
            {
                "type": "new_message_alert",
                "message": "You have a new message!",
            }
        )

        # Expect WebSocket message
        response = await self.communicator.receive_json_from()
        self.assertEqual(response, {
            "title": "New Message",
            "message": "You have a new message!",
        })

@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class ChatConsumerTest(TransactionTestCase):
    async def asyncSetUp(self):
        self.user1, self.user2, self.chat = await create_test_data()

        # User1's WebSocket connection
        self.user1_communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            f"/ws/chat/{self.chat.chat_id}/"
        )
        self.user1_communicator.scope["user"] = self.user1
        connected, _ = await self.user1_communicator.connect()
        self.assertTrue(connected)

        # User2's WebSocket connection
        self.user2_communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            f"/ws/chat/{self.chat.chat_id}/"
        )
        self.user2_communicator.scope["user"] = self.user2
        connected, _ = await self.user2_communicator.connect()
        self.assertTrue(connected)

    async def asyncTearDown(self):
        await self.user1_communicator.disconnect()
        await self.user2_communicator.disconnect()

    # Ensure messages are received in real-time by the other participant.
    async def test_send_and_receive_chat_message(self):
            await self.asyncSetUp()
            message_content = "Hello, this is a test message!"

            # User1 sends a message
            await self.user1_communicator.send_json_to({
                "message": message_content
            })

            # User2 receives the message
            response = await self.user2_communicator.receive_json_from()
            self.assertEqual(response["sender"], str(self.user1.account_uuid))
            self.assertEqual(response["message"], message_content)
            self.assertIsNotNone(response["timestamp"])