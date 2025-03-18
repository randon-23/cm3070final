from django.urls import path
from .views import *
from .api import *

app_name = 'chats'

urlpatterns = [
    ### View endpoints ###
    # path('chats/', chats_view, name='chats'),

    ### RESTful endpoints ###
    path('api/chats/get_chats/', get_chats, name='get_chats'),
    path('api/chats/get_messages/<str:chat_id>/', get_messages, name='get_messages'),
    path('api/chats/send_message/<str:chat_id>/', send_message, name='send_message'),
    path('api/chats/start_or_send_message/', start_or_send_message, name='start_or_send_message'),
    path('api/chats/mark_messages_read/<str:chat_id>/', mark_messages_read, name='mark_messages_read'),
]