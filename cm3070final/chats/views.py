from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from .api import get_chats, get_messages
from accounts_notifs.helpers import has_unread_notifications
from .helpers import has_unread_messages
from django.utils.dateparse import parse_datetime

@login_required
def chats_view(request):
    account = request.user
    context = {}
    context["has_unread_notifications"] = has_unread_notifications(account)
    context["has_unread_messages"] = has_unread_messages(account)

    chats_response = get_chats(request)
    context["chats"] = chats_response.data if chats_response.status_code == 200 else []

    messages_data = {}
    for chat in context["chats"]:
        messages_response = get_messages(request, chat["chat_id"])
        messages_data[chat["chat_id"]] = messages_response.data if messages_response.status_code == 200 else []

        # Assign the other participant for convenience
        p1 = chat["participant_1"]
        p2 = chat["participant_2"]
        chat["other_participant"] = p2 if p1["account_uuid"] == str(account.account_uuid) else p1

        other_participant = chat["other_participant"]
        if other_participant["volunteer"]:
            other_participant["profile_img"] = other_participant["volunteer"].get(
                "profile_img", static("images/default_volunteer.svg")
            )
        else:
            other_participant["profile_img"] = other_participant["organization"].get(
                "organization_profile_img", static("images/default_organization.svg")
            )

        # Add sender names to each message
        for message in messages_data[chat["chat_id"]]:
            if str(message["sender"]) == p1["account_uuid"]:
                sender = p1
            else:
                sender = p2

            if sender["volunteer"]:
                message["sender_name"] = f"{sender['volunteer']['first_name']} {sender['volunteer']['last_name']}"
                message["sender_profile_img"] = sender["volunteer"].get("profile_img", None)
            elif sender["organization"]:
                message["sender_name"] = sender["organization"]["organization_name"]
                message["sender_profile_img"] = sender["organization"].get("organization_profile_img", None)
            else:
                message["sender_name"] = "Unknown"
            message["timestamp"] = parse_datetime(message["timestamp"])

    context["messages"] = messages_data
    return render(request, "chats/chats.html", context)