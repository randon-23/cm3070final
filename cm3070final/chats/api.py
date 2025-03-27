from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from accounts_notifs.models import Account
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer

# Retrieve all chats for the authenticated user.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chats(request):
    user = request.user
    chats = Chat.objects.filter(participant_1=user) | Chat.objects.filter(participant_2=user)
    chats = chats.order_by('-last_updated_at')  # Sort by latest activity
    serializer = ChatSerializer(chats, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

# Retrieve all messages for a given chat.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, chat_id):
    try:
        chat = Chat.objects.get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user not in [chat.participant_1, chat.participant_2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    messages = Message.objects.filter(chat=chat).order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

# Send a new message in a chat.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, chat_id):
    try:
        chat = Chat.objects.get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user not in [chat.participant_1, chat.participant_2]:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    content = request.data.get('content', '').strip()
    if not content:
        return Response({'error': 'Message content cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    message = Message.objects.create(chat=chat, sender=request.user, content=content)

    return Response({'message': 'Message sent successfully'}, status=status.HTTP_201_CREATED)

# Start a chat if it doesn't exist & send the first message. Used mostly from the profile and opportunity when initiating messages.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_or_send_message(request):
    recipient_id = request.data.get("recipient_id")
    content = request.data.get("content", "").strip()

    if not recipient_id or not content:
        return Response({'error': 'Recipient and message content are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        recipient = Account.objects.get(account_uuid=recipient_id)
    except Account.DoesNotExist:
        return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

    # Prevent self-messaging
    if recipient == request.user:
        return Response({'error': 'You cannot message yourself'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if chat already exists (both orderings)
    chat = Chat.objects.filter(
        participant_1=request.user, participant_2=recipient
    ).first() or Chat.objects.filter(
        participant_1=recipient, participant_2=request.user
    ).first()

    # If chat doesn't exist, create it
    if not chat:
        chat = Chat.objects.create(participant_1=request.user, participant_2=recipient)

    # Send the message
    Message.objects.create(chat=chat, sender=request.user, content=content)

    return Response({'message': 'Message sent successfully'}, status=status.HTTP_201_CREATED)

# Mark all unread messages in a chat as read.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request, chat_id):
    try:
        chat = Chat.objects.get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user not in [chat.participant_1, chat.participant_2]:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    unread_messages = Message.objects.filter(chat=chat, is_read=False).exclude(sender=request.user)
    unread_messages.update(is_read=True)

    return Response({'message': 'Messages marked as read'}, status=status.HTTP_200_OK)
