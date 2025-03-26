from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message

# Send a WebSocket notification when a new message is received.
@receiver(post_save, sender=Message)
def notify_recipient_on_new_message(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat
        recipient = chat.participant_1 if instance.sender == chat.participant_2 else chat.participant_2        
        
        channel_layer = get_channel_layer()
        group_name = f"message_notifications_{recipient.account_uuid}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "new_message_alert",
                "message": "You have a new message!"
            }
        )