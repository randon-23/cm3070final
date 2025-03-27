from rest_framework import serializers
from .models import Chat, Message
from volunteers_organizations.serializers import UserDataSerializer

class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    participant_1 = UserDataSerializer(read_only=True)
    participant_2 = UserDataSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = ["chat_id", "participant_1", "participant_2", "last_updated_at", "last_message"]

    def get_last_message(self, obj):
        last_msg = Message.objects.filter(chat=obj).order_by('-timestamp').first()
        return last_msg.content if last_msg else None

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["message_id", "chat", "sender", "content", "timestamp", "is_read"]

    def validate(self, data):
        chat = data.get('chat')
        sender = data.get('sender')

        if sender not in [chat.participant_1, chat.participant_2]:
            raise serializers.ValidationError("Sender must be a participant in the chat")
        return data