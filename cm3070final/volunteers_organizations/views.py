from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Account
from .api import get_user_profile
from .forms import VolunteerForm, OrganizationForm
import json
    
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
        print(account)
        account.set_password(account_data.get('password'))
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

@login_required
def profile_view(request, account_uuid):
    is_own_profile = request.user.account_uuid == account_uuid
    context ={'is_own_profile': is_own_profile}
    if not is_own_profile:
        user_profile = get_user_profile(request, account_uuid)
        if user_profile.status_code==404:
            context['message'] = 'Profile not found'
        else:
            context['user_profile'] = json.loads(user_profile.content)
    return render(request, 'volunteers_organizations/profile.html', context)