from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Chat
from .api import get_chats, get_messages
from accounts_notifs.helpers import has_unread_notifications

# Create your views here.
@login_required
def chats_view(request):
    account = request.user
    context = {}
    has_unread = has_unread_notifications(account)
    context["has_unread_notifications"] = has_unread

    # Get the user's chats
    chats_response = get_chats(request)
    if chats_response.status_code == 404 or not chats_response.data:
        context["chats"] = []
    else:
        context["chats"] = chats_response.data

    # Get messages for each chat
    messages_data = {}
    for chat in context["chats"]:  # Iterate over the actual data, not response
        messages_response = get_messages(request, chat["chat_id"])
        if messages_response.status_code == 404 or not messages_response.data:
            messages_data[chat["chat_id"]] = []
        else:
            messages_data[chat["chat_id"]] = messages_response.data

    context["messages"] = messages_data

    return render(request, "chats/chats.html", context)