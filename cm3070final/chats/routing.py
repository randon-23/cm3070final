from django.urls import re_path
from .consumers import MessageNotificationConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/message_notifications/$", MessageNotificationConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<chat_id>[\w-]+)/$", ChatConsumer.as_asgi()),
]