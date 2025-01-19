from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import AccountSignupForm, LoginForm
import logging
logger=logging.getLogger(__name__)

def account_signup(request):
    if request.method == 'POST':
        form = AccountSignupForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False) # Not committing to the database yet as we need to navigate to volunteer/organization details and collect those so to not create an Account object which is not linked to a Volunteer or Organization object
            logger.info("Accound data being saved to session: %s", form.cleaned_data)
            request.session['account_data']=form.cleaned_data
            if account.user_type=='volunteer':
                return redirect('volunteer_signup')
            elif account.user_type=='organization':
                return redirect('organization_signup')
    else:
        form=AccountSignupForm()
    return render(request, 'accounts_notifs/account_signup.html', {'form': form})
        
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username=form.get_cleaned_data('username')
            password=form.get_cleaned_data('password')
            user=authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form=LoginForm()
    return render(request, 'accounts_notifs/login.html', {'form': form})
    