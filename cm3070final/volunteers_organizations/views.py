from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Account
from .forms import VolunteerForm, OrganizationForm
    
def signup_final(request):
    account_data=request.session.get('account_data')

    if not account_data:
        return redirect('accounts_notifs:authentication', type='signup')
    
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

        return render(request, 'volunteers_organizations/partials/signup_success_modal.html', status=200)
    
    return render(request, 'volunteers_organizations/signup_final.html', {
        'form': form,
        'user_type': user_type
    })