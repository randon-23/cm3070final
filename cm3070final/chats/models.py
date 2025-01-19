from django.db import models
from accounts_notifs.models import Account
import uuid
from django.core.exceptions import ValidationError

# This means Participant 1 will be the user who initiated the chat
class Chat(models.Model):
    chat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant_1 = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='chat_participant_1')
    participant_2 = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='chat_participant_2')
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['participant_1', 'participant_2'],
                name='unique_chat_between_participants'
            )
        ]

    def clean(self):
        # Checking if chat exists between users in reverse order
        if Chat.objects.filter(participant_1=self.participant_2, participant_2=self.participant_1).exists():
            raise ValidationError("Chat between participants already exists")
        super().clean()
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(Account, on_delete=models.CASCADE)
    content = models.TextField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def clean(self):
        # Ensuring sender is a participant in the chat
        if self.sender not in [self.chat.participant_1, self.chat.participant_2]:
            raise ValidationError("Sender must be a participant in the chat.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
