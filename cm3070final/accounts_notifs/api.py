from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

Account = get_user_model()

@api_view(['POST'])
def login_api(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email_address=email, password=password)
    if user is not None:
        login(request, user)
        return Response({'message': 'Login successful!'}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_api(request):
    logout(request)
    return Response({'message': 'Logout successful!'}, status=status.HTTP_200_OK)

class PasswordResetRequestEndpoint(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        account = Account.objects.filter(email_address=email).first()
        if not account:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
        
        token = default_token_generator.make_token(account)
        reset_link = request.build_absolute_uri(reverse('accounts_notifs:password_reset')) + f'?user={account.account_uuid}&token={token}&reset_stage=confirm'

        send_mail(
            'Password Reset Request',
            'Click the link below to reset your password:\n' + reset_link,
            'volonteracm3070@gmail.com',
            [email],
            fail_silently=False
        )

        return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)
    
class PasswordResetConfirmEndpoint(APIView):
    def post(self, request):
        user = request.data.get('user')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user:
            return Response({'error': 'User is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        if not token:
            return Response({'error': 'Unauthorized request'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not new_password:
            return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        account = Account.objects.filter(account_uuid=user).first()
        if not account or not default_token_generator.check_token(account, token):
            return Response({'error': 'Invalid token and/or user'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            validate_password(new_password, account)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
        
        account.set_password(new_password)
        account.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)