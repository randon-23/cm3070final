from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from rest_framework.views import APIView
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.core.exceptions import ValidationError
from accounts_notifs.models import Account
from .models import Volunteer, Organization, Following, Endorsement, StatusPost
from accounts_notifs.serializers import AccountSerializer
from .serializers import VolunteerSerializer, OrganizationSerializer, FollowingCreateSerializer, EndorsementSerializer, StatusPostSerializer


# Designed to get both Account and related Volunteer/Organization model data
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, account_uuid):
    try:
        account = Account.objects.get(account_uuid=account_uuid)
    except Account.DoesNotExist:
        return Response({'message': 'Account not found'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        account_serializer = AccountSerializer(account)
        if account.is_volunteer():
            try:
                volunteer = Volunteer.objects.get(account=account)
                volunteer_serializer = VolunteerSerializer(volunteer)
                return JsonResponse({
                    'account': account_serializer.data,
                    'volunteer': volunteer_serializer.data
                }, safe=False)
            except Volunteer.DoesNotExist:
                return Response({'message': 'Volunteer profile not found'},status=status.HTTP_404_NOT_FOUND)
        elif account.is_organization():
            try:
                organization = Organization.objects.get(account=account)
                organization_serializer = OrganizationSerializer(organization)
                return JsonResponse({
                    'account': account_serializer.data,
                    'organization': organization_serializer.data
                }, safe=False)
            except Organization.DoesNotExist:
                return Response({'message': 'Organization profile not found'},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message': 'Account type not found'},status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'message': 'Method not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)

### FOLLOWING ###
# Get all followers of a given account    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_followers(request, account_uuid):
    try:
        account = Account.objects.get(account_uuid=account_uuid)
    except Account.DoesNotExist:
        return Response({'message': 'Account not found'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        followers = Following.objects.filter(
            models.Q(followed_volunteer__account=account) |
            models.Q(followed_organization__account=account)
        )

        follower_count = followers.count()

        return Response({'followers': follower_count})
    else:
        return Response({'message': 'Method not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Get whether the authenticated user follows a given account
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request, account_uuid):
    user = request.user
    followed_account = Account.objects.filter(account_uuid=account_uuid).first()
    if not followed_account:
        return Response({'message': 'Account not found'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        is_following = Following.objects.filter(
            follower=user,
            followed_volunteer=followed_account.volunteer if followed_account.is_volunteer() else None,
            followed_organization=followed_account.organization if followed_account.is_organization() else None
        ).exists() # Returns True if exists, False otherwise

        return Response({'is_following': is_following})
    else:
        return Response({'message': 'Method not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_following(request, account_uuid):
    follower = request.user

    followed_account = Account.objects.filter(account_uuid=account_uuid).first()
    if not followed_account:
        return Response({'message': 'Account not found'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'POST':
        followed_volunteer = followed_account.volunteer if followed_account.is_volunteer() else None
        followed_organization = followed_account.organization if followed_account.is_organization() else None

        data = {'followed_volunteer': followed_volunteer, 'followed_organization': followed_organization}
        serializer = FollowingCreateSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            serializer.save()

            followers_count = Following.objects.filter(
                models.Q(followed_volunteer=followed_volunteer) |
                models.Q(followed_organization=followed_organization)
            ).count()

            return Response({'message': 'Followed successfully', 'followers_count': followers_count, "is_following": True}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Method not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)

#User unfollows
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_following(request, account_uuid):
    follower = request.user

    followed_account = Account.objects.filter(account_uuid=account_uuid).first()
    if not followed_account:
        return Response({'message': 'Account not found'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'DELETE':
        followed_volunteer = followed_account.volunteer if followed_account.is_volunteer() else None
        followed_organization = followed_account.organization if followed_account.is_organization() else None

        following = Following.objects.filter(
            follower=follower,
            followed_volunteer=followed_volunteer,
            followed_organization=followed_organization
        )

        if not following:
            return Response({'message': 'Following not found'},status=status.HTTP_404_NOT_FOUND)
        
        following.delete()

        followers_count = Following.objects.filter(
            models.Q(followed_volunteer=followed_volunteer) |
            models.Q(followed_organization=followed_organization)
        ).count()

        return Response({'message': 'Unfollowed successfully', 'followers_count': followers_count, 'is_following': False}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Method not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
### ENDORSEMENTS ###
#Get All Endorsements for a User
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_endorsements(request, account_uuid):
    endorsements = Endorsement.objects.filter(receiver__account_uuid=account_uuid).order_by("-created_at")
    serializer = EndorsementSerializer(endorsements, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Create an Endorsement
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_endorsement(request, account_uuid):
    data = request.data.copy()
    data["receiver"] = account_uuid  # Inject receiver
    serializer = EndorsementSerializer(data=data, context={"request": request})
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Delete an Endorsement
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_endorsement(request, id):
    endorsement = Endorsement.objects.filter(id=id).first()
    
    if not endorsement:
        return Response({"message": "Endorsement not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if endorsement.giver != request.user:
        return Response({"message": "You are not authorized to delete this endorsement."}, status=status.HTTP_403_FORBIDDEN)
    
    endorsement.delete()
    return Response({"message": "Endorsement deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

#Get All Status Posts for a User
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_status_posts(request, account_uuid):
    status_posts = StatusPost.objects.filter(author__account_uuid=account_uuid).order_by("-created_at")
    serializer = StatusPostSerializer(status_posts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Create a Status Post
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_status_post(request):
    serializer = StatusPostSerializer(data=request.data, context={"request": request})
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Delete a Status Post
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_status_post(request, id):
    try:
        status_post = StatusPost.objects.get(id=id)
    except StatusPost.DoesNotExist:
        return Response({"message": "Status post not found"}, status=status.HTTP_404_NOT_FOUND)

    status_post.delete()
    return Response({"message": "Status post deleted"}, status=status.HTTP_204_NO_CONTENT)