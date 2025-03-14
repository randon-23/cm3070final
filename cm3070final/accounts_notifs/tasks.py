from celery import shared_task
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

Account = get_user_model()

@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def send_notification(recipient_id, notification_type, message):
    try:
        recipient = Account.objects.get(account_uuid=recipient_id)
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            notification_message=message
        )

        # Send real-time notification via WebSockets
        channel_layer = get_channel_layer()
        group_name = f"user_notifications_{recipient_id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "new.notification",
                "message": message,
                "title": notification_type.replace("_", " ").title(),
            }
        )
    except Account.DoesNotExist:
        pass