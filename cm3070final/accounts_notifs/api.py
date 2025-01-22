from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def login_api(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email_address=email, password=password)
    if user is not None:
        login(request, user)
        return Response({'message': 'Login successful!'}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)