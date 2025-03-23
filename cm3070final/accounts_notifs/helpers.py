from .models import Notification

def has_unread_notifications(account):
    return Notification.objects.filter(recipient=account, is_read=False).exists()