from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from .forms import AccountSignupForm, LoginForm, AccountSignupFormSSO
from phonenumbers.data import _COUNTRY_CODE_TO_REGION_CODE
from django.contrib.auth.decorators import login_required
from .api import get_notifications
from django.core.paginator import Paginator
from datetime import datetime
from django.utils.dateparse import parse_datetime
from .helpers import has_unread_notifications

def authentication_view(request):
    country_prefixes = [
        (f"+{code}", f"+{code}")
        for code in _COUNTRY_CODE_TO_REGION_CODE.keys()
    ]
    country_prefixes.sort(key=lambda x: int(x[0][1:]))  # Sort by numerical value of the prefix
    form_type = request.GET.get('type', 'login')  # Default to 'login' if no type is specified

    if request.method == 'POST':
        if form_type == 'signup':
            # Google Email is stored in session if user is redirected from Google login
            google_email = request.session.get('google_email', None)
            if not google_email:
                form = AccountSignupForm(request.POST)
                if form.is_valid():
                    # account = form.save(commit=False) dont need to differentiate between volunteer and organization at this stage due to change in template (from 2 into 1) all we need is the account data
                    cleaned_data = form.cleaned_data

                    password = cleaned_data.pop('password_1')
                    cleaned_data.pop('password_2')
                    cleaned_data['password'] = password
                    request.session['account_data'] = cleaned_data
                    print(request.session['account_data'])

                    return redirect('volunteers_organizations:signup_final')
                else:
                    return render(request, 'accounts_notifs/authentication.html', {
                        'form': form,
                        'form_type': form_type,
                        "country_prefixes": country_prefixes,
                    })
            else:
                form = AccountSignupFormSSO(request.POST)
                if form.is_valid():
                    cleaned_data = form.cleaned_data
                    cleaned_data['email_address'] = google_email
                    cleaned_data['password'] = make_password(None)

                    request.session['account_data'] = cleaned_data

                    return redirect('volunteers_organizations:signup_final')
                else:
                    return render(request, 'accounts_notifs/authentication.html', {
                        'form': form,
                        'form_type': form_type,
                        "country_prefixes": country_prefixes,
                    })
        elif form_type == 'login': 
            form = LoginForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('volunteers_organizations:profile', account_uuid=user.account_uuid)
                else:
                    form.add_error(None, 'Invalid email address or password')
            else:
                return render(request, 'accounts_notifs/authentication.html', {
                    'form': form,
                    'form_type': form_type,
                })
    form = AccountSignupForm() if form_type == 'signup' else LoginForm()           

    return render(request, 'accounts_notifs/authentication.html', {
        'form': form,
        'form_type': form_type,
        "country_prefixes": country_prefixes,
    })

def password_reset_view(request):
    reset_stage = request.GET.get('reset_stage', 'request')
    return render(request, 'accounts_notifs/password_reset.html', {'reset_stage': reset_stage})

@login_required
def notifications_view(request):
    account = request.user
    has_unread = has_unread_notifications(account)
    notifications_response = get_notifications(request, account.account_uuid)

    if notifications_response.status_code != 200:
        return render(request, 'base/base_error.html', {
            "status_code": notifications_response.status_code
        }, status=notifications_response.status_code)

    notifications = notifications_response.data

    # Convert created_at to datetime
    for notif in notifications:
        if isinstance(notif["created_at"], str):
            notif["created_at"] = parse_datetime(notif["created_at"])

    # Paginate notifications (20 per page)
    page = request.GET.get("page", 1)
    paginator = Paginator(notifications, 20)
    paginated_notifications = paginator.get_page(page)

    return render(request, 'accounts_notifs/notifications.html', {
        "notifications": paginated_notifications,
        "has_unread_notifications": has_unread,
    })