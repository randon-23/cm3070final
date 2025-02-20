from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth import get_backends
from accounts_notifs.models import Account
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from allauth.exceptions import ImmediateHttpResponse

class GoogleSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # For some reason when user is new and email is not verified, the email is stored in sociallogin.user.email
        # Otherwise, the email is stored in sociallogin.user
        if '@' in sociallogin.user.email:
            email = sociallogin.user.email
        else:
            email = sociallogin.user
        print(sociallogin)
        print(sociallogin.user)
        print(sociallogin.user.email)
        print(email)
        try:
            print("Email used: ", email)
            account = Account.objects.get(email_address=email)
            account_uuid = account.account_uuid
            print(account_uuid)
            print('1')
            # Check if the user is already linked to Google
            if not SocialAccount.objects.filter(user=account, provider='google').exists():
                # Link the Google account to the existing userr
                print('2')
                sociallogin.connect(request, account)
        
            backend = get_backends()[1]  # Get the authentication backend
            account.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, account) # Log the user in
            raise ImmediateHttpResponse(redirect(f'/volunteers-organizations/profile/{account_uuid}')) # Redirect to profile, bypassing LOGIN_REDIRECT_URL
        except Account.DoesNotExist:
            # No user exists → Redirect to partial signup with email prefilled
            print('3')
            request.session['google_email'] = email
            print(request.session['google_email'])
            raise ImmediateHttpResponse(redirect('/accounts/auth/?type=signup'))