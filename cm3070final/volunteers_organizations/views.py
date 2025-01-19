from django.shortcuts import render, get_object_or_404, redirect
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
    
