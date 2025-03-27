from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from accounts_notifs.models import Account
from .models import Volunteer, Organization, Following, Endorsement, StatusPost, VolunteerMatchingPreferences, OrganizationPreferences
from accounts_notifs.serializers import AccountSerializer
from .serializers import VolunteerSerializer, OrganizationSerializer, FollowingCreateSerializer, EndorsementSerializer, StatusPostSerializer, VolunteerMatchingPreferencesSerializer, OrganizationPreferencesSerializer
import json
import ast
from django.http import QueryDict

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
                if VolunteerMatchingPreferences.objects.filter(volunteer=volunteer).exists():
                    volunteer_preferences = VolunteerMatchingPreferencesSerializer(volunteer.volunteermatchingpreferences)
                    return JsonResponse({
                        'account': account_serializer.data,
                        'volunteer': volunteer_serializer.data,
                        'preferences': volunteer_preferences.data
                    }, safe=False)
                else:
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
                if OrganizationPreferences.objects.filter(organization=organization).exists():
                    organization_preferences = OrganizationPreferencesSerializer(organization.organizationpreferences)
                    return JsonResponse({
                        'account': account_serializer.data,
                        'organization': organization_serializer.data,
                        'preferences': organization_preferences.data
                    }, safe=False)
                else:
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

#User follows
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
                models.Q(followed_volunteer__account=followed_account) |
                models.Q(followed_organization__account=followed_account)
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
            models.Q(followed_volunteer__account=followed_account) |
            models.Q(followed_organization__account=followed_account)
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
    serializer = EndorsementSerializer(endorsements, many=True, context={"request": request})
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
        return Response({"message": "Endorsement created successfully!", "data": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response({"message": "Error occurred", "data": serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

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
    serializer = StatusPostSerializer(status_posts, many=True, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)

#Create a Status Post
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_status_post(request):
    serializer = StatusPostSerializer(data=request.data, context={"request": request})
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Status post created successfully!", "data": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response({"message": "Error occurred", "data": serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

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

### SEARCH RESULTS - volunteers and organizations ###
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_search_profiles(request):
    if request.method != "GET":
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    query = request.GET.get("q", "").strip()
    if not query:
        return Response({"results": []})
    
    volunteers = Volunteer.objects.annotate(
        full_name=Concat(F("first_name"), Value(" "), F("last_name"))
    ).filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) | 
        Q(full_name__icontains=query)
    ).select_related("account")[:10]

    organizations = Organization.objects.filter(
        Q(organization_name__icontains=query)
    ).select_related("account")[:10]

    volunteer_serializer = VolunteerSerializer(volunteers, many=True)
    organization_serializer = OrganizationSerializer(organizations, many=True)

    results = volunteer_serializer.data + organization_serializer.data

    return Response({
        "results": results
    }, status=status.HTTP_200_OK)

### VOLUNTEER MATCHING PREFERENCES ###
# Creates VolunteerMatchingPreferences for a volunteer. If preferences already exist, return an error.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_volunteer_preferences(request):
    if request.method == 'POST':
        try:
            volunteer = Volunteer.objects.get(account=request.user)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Only volunteers can set preferences'}, status=status.HTTP_403_FORBIDDEN)
        
        if VolunteerMatchingPreferences.objects.filter(volunteer=volunteer).exists():
            return Response({'error': 'Preferences already set'}, status=status.HTTP_409_CONFLICT)
        
        # Convert QueryDict to JSON-compatible dictionary
        if isinstance(request.data, QueryDict):
            data = request.data.copy()
            formatted_data = {}

            for key, value in data.lists():
                if key == "preferred_work_types":
                    formatted_data[key] = value[0] if value else None
                elif key == "location":
                    try:
                        formatted_data[key] = json.loads(value[0]) if isinstance(value[0], str) else value[0]
                    except json.JSONDecodeError:
                        return Response({'error': 'Invalid JSON for location field'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    formatted_data[key] = value
        else:
            formatted_data = request.data
        
        serializer = VolunteerMatchingPreferencesSerializer(data=formatted_data, context={'request': request})
        if serializer.is_valid():
            serializer.save(volunteer=volunteer)
            return Response({"message": "Successfully created volunteer matching preferences", "data": serializer.data}, status=status.HTTP_201_CREATED)
        print("Serializer Errors:", serializer.errors)
        return Response({"message": "An error occurred creating volunteer matching preferences", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_volunteer_preferences(request):
    if request.method == 'GET':
        if request.user.is_volunteer():
            preferences = VolunteerMatchingPreferences.objects.filter(volunteer__account=request.user).first()
            if preferences:
                serializer = VolunteerMatchingPreferencesSerializer(preferences, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Volunteer preferences not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message': 'Only volunteers can view volunteer preferences'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_volunteer_preferences(request):
    if request.method == 'PATCH':
        try:
            volunteer = Volunteer.objects.get(account=request.user)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Only volunteers can update preferences'}, status=status.HTTP_403_FORBIDDEN)
        
        preferences = VolunteerMatchingPreferences.objects.filter(volunteer=volunteer).first()
        if not preferences:
            return Response({'error': 'Volunteer preferences not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Convert QueryDict to JSON-compatible dictionary
        if isinstance(request.data, QueryDict):
            data = request.data.copy()
            formatted_data = {}

            for key, value in data.lists():
                if key == "preferred_work_types":
                    formatted_data[key] = value[0] if value else None
                elif key == "location":
                    try:
                        #Formatting location field to match existing JSON format
                        location_str = value[0]
                        if "'" in location_str and not '"' in location_str:
                            location_str = location_str.replace("'", '"')
                        parsed_location = ast.literal_eval(location_str)
                        formatted_data[key] = json.loads(json.dumps(parsed_location))
                    except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                        return Response({'error': 'Invalid JSON for location field'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    formatted_data[key] = value
        else:
            formatted_data = request.data
        
        serializer = VolunteerMatchingPreferencesSerializer(preferences, data=formatted_data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Successfully updated volunteer preferences", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "An error occurred updating volunteer preferences", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


### ORGANIZATION PREFERENCES ###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_organization_preferences(request):
    if request.method == 'POST':
        try:
            organization = Organization.objects.get(account=request.user)
        except Organization.DoesNotExist:
            return Response({'error': 'Only organizations can set preferences'}, status=status.HTTP_403_FORBIDDEN)

        if OrganizationPreferences.objects.filter(organization=organization).exists():
            return Response({'error': 'Preferences already set'}, status=status.HTTP_409_CONFLICT)

        # Convert QueryDict to JSON-compatible dictionary
        if isinstance(request.data, QueryDict):
            data = request.data.copy()
            formatted_data = {}

            for key, value in data.lists():
                if key == "location":
                    try:
                        formatted_data[key] = json.loads(value[0]) if isinstance(value[0], str) else value[0]
                    except json.JSONDecodeError:
                        return Response({'error': 'Invalid JSON for location field'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    formatted_data[key] = value[0] if value else None
        else:
            formatted_data = request.data

        serializer = OrganizationPreferencesSerializer(data=formatted_data, context={'request': request})
        if serializer.is_valid():
            serializer.save(organization=organization)
            return Response({"message": "Successfully created organization preferences", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": "An error occurred creating organization preferences", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_preferences(request):
    if request.method == 'GET':
        if request.user.is_organization():
            preferences = OrganizationPreferences.objects.filter(organization__account=request.user).first()
            if preferences:
                serializer = OrganizationPreferencesSerializer(preferences, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Organization preferences not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message': 'Only organizations can view organization preferences'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_organization_preferences(request):
    if request.method == 'PATCH':
        try:
            organization = Organization.objects.get(account=request.user)
        except Organization.DoesNotExist:
            return Response({'error': 'Only organizations can update preferences'}, status=status.HTTP_403_FORBIDDEN)

        preferences = OrganizationPreferences.objects.filter(organization=organization).first()
        if not preferences:
            return Response({'error': 'Organization preferences not found'}, status=status.HTTP_404_NOT_FOUND)

        # Convert QueryDict to JSON-compatible dictionary
        if isinstance(request.data, QueryDict):
            data = request.data.copy()
            formatted_data = {}

            for key, value in data.lists():
                if key == "location":
                    try:
                        #Formatting location field to match existing JSON format
                        location_str = value[0]
                        if "'" in location_str and not '"' in location_str:
                            location_str = location_str.replace("'", '"')
                        parsed_location = ast.literal_eval(location_str)
                        formatted_data[key] = json.loads(json.dumps(parsed_location))
                    except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                        return Response({'error': 'Invalid JSON for location field'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    formatted_data[key] = value[0] if value else None
        else:
            formatted_data = request.data

        serializer = OrganizationPreferencesSerializer(preferences, data=formatted_data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Successfully updated organization preferences", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response({"message": "An error occurred updating organization preferences", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def donate_volontera_points(request, organization_id):
    if request.method == 'POST':
        volunteer = request.user.volunteer  
        amount = request.data['amount']  # Extract from request body

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Donation amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)
        
        if volunteer.volontera_points < amount:
            return Response({"error": "Not enough points"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            organization = Organization.objects.get(account__account_uuid=organization_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Transfer the points
        volunteer.volontera_points -= amount
        organization.volontera_points += amount

        volunteer.save()
        organization.save()

        return Response({"message": f"Successfully donated {amount} points!"}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)