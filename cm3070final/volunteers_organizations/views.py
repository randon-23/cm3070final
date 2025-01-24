from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Account
from .forms import VolunteerForm, OrganizationForm

def volunteer_signup(request):
    account_data = request.session.get('account_data')
    if not account_data:
        return redirect('account_signup')
    if request.method == 'POST':
        form = VolunteerForm(request.POST)
        if form.is_valid():
            account=Account(**account_data)
            account.save()

            volunteer=form.save(commit=False)
            volunteer.account=account
            volunteer.save()
            del request.session['account_data'] # Clearing the session data
            return redirect('login')
    else:
        form = VolunteerForm()
    return render(request, 'volunteer_organization/volunteer_signup.html', {'form': form})

def organization_signup(request):
    account_data=request.session.get('account_data')
    if not account_data:
        return redirect('account_signup')
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            account=Account(**account_data)
            account.save()

            organization=form.save(commit=False)
            organization.account=account
            organization.save()
            del request.session['account_data']
            return redirect('login')
    else:
        form = OrganizationForm()
    return render(request, 'volunteer_organization/organization_signup.html', {'form': form})
    
def signup_next(request):
    account_data=request.session.get('account_data')

    if not account_data:
        return redirect('authentication')
    
    user_type=account_data.get('user_type')
    form=None

    if user_type=='volunteer':
        form=VolunteerForm(request.POST or None)
    elif user_type=='organization':
        form=OrganizationForm(request.POST or None)

    if request.method=='POST' and form.is_valid():
        account = Account(**account_data)
        account.set_password(account_data.get('password_1'))
        account.save()

        user=form.save(commit=False)
        user.account=account
        user.save()
        request.session.pop('account_data', None)
        return HttpResponseRedirect(reverse('authentication')+f'?type=login')