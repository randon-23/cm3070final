from django.db.models import Q
from chats.models import Message

def has_unread_messages(account):
    return Message.objects.filter(
        Q(chat__participant_1=account) | Q(chat__participant_2=account),
        ~Q(sender=account),
        is_read=False
    ).exists()