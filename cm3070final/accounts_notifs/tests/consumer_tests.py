from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from channels.routing import URLRouter
from django.test import override_settings
from django.test import TransactionTestCase
from channels.db import database_sync_to_async
from ..routing import websocket_urlpatterns
from channels.auth import AuthMiddlewareStack
from channels.layers import get_channel_layer

Account = get_user_model()

@database_sync_to_async
def create_test_data():
    organization_account = Account.objects.create_user(email_address="org@test.com", password="org_password", user_type="organization", contact_number="+1234567892")
    return organization_account

@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class NotificationConsumerTest(TransactionTestCase):
    async def asyncSetUp(self):
        self.organization_account = await create_test_data()

        # Set up WebSocket communicator
        self.communicator = WebsocketCommunicator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns)), f"ws/notifications/")

        # Properly set authentication in scope
        self.communicator.scope["user"] = self.organization_account

        connected, _ = await self.communicator.connect()
        self.assertTrue(connected, "WebSocket connection failed!")

    async def asyncTearDown(self):
        await self.communicator.disconnect()

    # Only need one test to verify that the consumer is working as expected
    async def test_websocket_message_is_received(self):
        await self.asyncSetUp()
        org_notification_group = f"user_notifications_{self.organization_account.account_uuid}"

        # Implicitly confirms that the consumer is listening for new notifications on the correctly named group
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            org_notification_group,
            {
                "type": "new.notification",
                "message": "Jane Doe has applied to Community Cleanup.",
                "title": "Application Submitted",
            }
        )
        # Receive WebSocket response
        response = await self.communicator.receive_json_from()

        # Verify received message
        self.assertEqual(response["title"], "Application Submitted")
        self.assertEqual(response["message"], "Jane Doe has applied to Community Cleanup.")

