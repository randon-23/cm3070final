from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from .forms import AccountSignupForm, LoginForm, AccountSignupFormSSO
from phonenumbers.data import _COUNTRY_CODE_TO_REGION_CODE

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
            print(google_email)
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

                    return redirect('signup_final')
                else:
                    return render(request, 'accounts_notifs/authentication.html', {
                        'form': form,
                        'form_type': form_type,
                        "country_prefixes": country_prefixes,
                    })
            else:
                print('hello')
                form = AccountSignupFormSSO(request.POST)
                if form.is_valid():
                    print('salam')
                    cleaned_data = form.cleaned_data
                    cleaned_data['email_address'] = google_email
                    cleaned_data['password'] = make_password(None)

                    request.session['account_data'] = cleaned_data
                    print(request.session['account_data'])

                    return redirect('signup_final')
                else:
                    print('fail lol')
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
                    return redirect('dashboard')
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