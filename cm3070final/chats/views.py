from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Chat
from .api import get_chats, get_messages

# Create your views here.
@login_required
def chats_view(request):
    account = request.user
    chats_data = get_chats(request)

    messages_data = {}
    for chat in chats_data:
        messages = get_messages(request, chat.chat_id)
        messages_data[chat.chat_id] = messages

    return render(request, "chats/chats.html", {
        "chats": chats_data,
        "messages": messages_data
    })