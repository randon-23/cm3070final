import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import Chat, Message

class MessageNotificationConsumer(AsyncWebsocketConsumer):
    # Connect user to their message notification channel
    async def connect(self):
        Account = get_user_model()
        self.user = self.scope["user"]
        print(f"Connecting Message Notification WebSocket for user: {self.user}")

        if isinstance(self.user, Account) and self.user.is_authenticated:
            print(f"Authenticated user: {self.user}")
            self.notification_group = f"message_notifications_{self.user.account_uuid}"
            print(f"User {self.user.email_address} connected to group: {self.notification_group}")
            await self.channel_layer.group_add(self.notification_group, self.channel_name)
            await self.accept()
        else:
            await self.close()

    # Remove user from notification group on disconnect
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.notification_group, self.channel_name)

    # Send a message alert to the user
    async def new_message_alert(self, event):
        message = event["message"]
        title = "New Message"
        await self.send(text_data=json.dumps({
            "title": title,
            "message": message
        }))

# When a user connects, join the WebSocket group for this chat.
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_group_name = f"chat_{self.chat_id}"

        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if the user is a participant in this chat
        chat = await database_sync_to_async(self.get_chat, thread_sensitive=True)()
        if not chat:
            await self.close()
            return

        # Add user to the chat WebSocket group
        await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
        await self.accept()

    # Remove user from the WebSocket group when they disconnect.
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)

    # Handle incoming messages.
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data["message"]

        # Save message to DB
        message = await database_sync_to_async(self.create_message)(message_content)
        if message:
            sender_name = await database_sync_to_async(self.get_sender_name)()
            sender_profile_img = await database_sync_to_async(self.get_sender_profile_img)()
        # Send message to WebSocket group
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                "type": "chat.message",
                "sender": str(self.user.account_uuid),
                "sender_name": sender_name,
                "sender_profile_img": sender_profile_img,
                "message": message_content,
                "timestamp": message.timestamp.isoformat(),
            }
        )

    # Send message to WebSocket clients.
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "sender_name": event["sender_name"],
            "sender_profile_img": event["sender_profile_img"],
            "message": event["message"],
            "timestamp": event["timestamp"],
        }))

    # Check chat membership
    def get_chat(self):
        return Chat.objects.filter(
            chat_id=self.chat_id,
            participant_1=self.user
        ).first() or Chat.objects.filter(
            chat_id=self.chat_id,
            participant_2=self.user
        ).first()

    # Create and save the message in the database.
    def create_message(self, content):
        chat = Chat.objects.filter(chat_id=self.chat_id).first()
        if chat:
            return Message.objects.create(chat=chat, sender=self.user, content=content)
        return None
    
    def get_sender_name(self):
        if hasattr(self.user, "volunteer") and self.user.volunteer:
            return f"{self.user.volunteer.first_name} {self.user.volunteer.last_name}"
        elif hasattr(self.user, "organization") and self.user.organization:
            return self.user.organization.organization_name
        return "Unknown"

    def get_sender_profile_img(self):
        if hasattr(self.user, "volunteer") and self.user.volunteer and self.user.volunteer.profile_img:
            return self.user.volunteer.profile_img.url
        elif hasattr(self.user, "organization") and self.user.organization and self.user.organization.organization_profile_img:
            return self.user.organization.organization_profile_img.url
        return ""