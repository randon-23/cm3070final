from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.core.exceptions import ValidationError
from accounts_notifs.models import Account
from .serializers import AccountSerializer, VolunteerSerializer, OrganizationSerializer

# Designed to get both Account and related Volunteer/Organization model data
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, account_uuid):
    try:
        account = Account.objects.get(uuid=account_uuid)
    except Account.DoesNotExist:
        return Response({'message': 'Account not found'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        account_serializer = AccountSerializer(account)
        if account.is_volunteer:
            volunteer = account.volunteer
            volunteer_serializer = VolunteerSerializer(volunteer)
            return JsonResponse({
                'account': account_serializer.data,
                'volunteer': volunteer_serializer.data
            })
        elif account.is_organization:
            organization = account.organization
            organization_serializer = OrganizationSerializer(organization)
            return JsonResponse({
                'account': account_serializer.data,
                'organization': organization_serializer.data
            })
    else:
        return Response({'message': 'Method not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)