from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import AccountSignupForm, LoginForm
from phonenumbers.data import _COUNTRY_CODE_TO_REGION_CODE
import logging
logger=logging.getLogger(__name__)

def authentication_view(request):
    country_prefixes = [
        (f"+{code}", f"+{code}")
        for code in _COUNTRY_CODE_TO_REGION_CODE.keys()
    ]
    country_prefixes.sort(key=lambda x: int(x[0][1:]))  # Sort by numerical value of the prefix
    form_type = request.GET.get('type', 'login')  # Default to 'login' if no type is specified

    if request.method == 'POST':
        if form_type == 'signup':
            form = AccountSignupForm(request.POST)
            if form.is_valid():
                # account = form.save(commit=False) dont need to differentiate between volunteer and organization at this stage due to change in template (from 2 into 1) all we need is the account data
                logger.info("Account data being saved to session: %s", form.cleaned_data)
                request.session['account_data'] = form.cleaned_data

                return redirect('signup_final')
            else:
                return render(request, 'accounts_notifs/authentication.html', {
                    'form': form,
                    'form_type': form_type,
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