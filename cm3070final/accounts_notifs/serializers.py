from rest_framework import serializers
from .models import Account, Notification

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["account_uuid", "email_address", "contact_number", "user_type", "created_at"]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["notification_uuid" ,"recipient","notification_type", "notification_message", "created_at"]