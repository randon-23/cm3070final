from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import AccountSignupForm, LoginForm
import logging
logger=logging.getLogger(__name__)

def authentication_view(request):
    form_type = request.GET.get('type', 'login')  # Default to 'login' if no type is specified
    form = AccountSignupForm() if form_type == 'signup' else LoginForm()

    if request.method == 'POST':
        if form_type == 'signup':
            form = AccountSignupForm(request.POST)
            if form.is_valid():
                account = form.save(commit=False)
                logger.info("Account data being saved to session: %s", form.cleaned_data)
                request.session['account_data'] = form.cleaned_data
                if account.user_type == 'volunteer':
                    return redirect('volunteer_signup')
                elif account.user_type == 'organization':
                    return redirect('organization_signup')
        elif form_type == 'login':
            form = LoginForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('dashboard')

    return render(request, 'accounts_notifs/authentication.html', {
        'form': form,
        'form_type': form_type,
    })