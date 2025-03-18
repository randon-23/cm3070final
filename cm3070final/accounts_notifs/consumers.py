import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

class NotificationConsumer(AsyncWebsocketConsumer):
    # Handles new WebSocket connections
    async def connect(self):
        Account = get_user_model()
        self.user = self.scope["user"]
        print(f"Connecting Notification WebSocket for user: {self.user}")
        
        # Authenticate user
        if isinstance(self.user, Account) and self.user.is_authenticated:
            print(f"Authenticated user: {self.user}")
            self.user_group = f"user_notifications_{self.user.account_uuid}"
            print(f"User {self.user.email_address} connected to group: {self.user_group}") 
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            await self.accept()
        else:
            await self.close()

    # Handles WebSocket disconnections
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    # Handles incoming notifications from the backend (via Celery tasks/signals)
    async def new_notification(self, event):
        message = event["message"]
        title = event.get("title", "New Notification")

        await self.send(text_data=json.dumps({
            "title": title,
            "message": message
        }))