from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Account
from .api import get_user_profile, get_following, get_all_followers, get_status_posts, get_endorsements, get_search_profiles
from .forms import VolunteerForm, OrganizationForm
from .models import Volunteer, Organization, VolunteerMatchingPreferences
import json
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
    
def signup_final(request):
    account_data=request.session.get('account_data')

    if not account_data:
        return redirect('accounts_notifs:authentication', type='signup')
    
    user_type=account_data.get('user_type')
    form=None

    if user_type=='volunteer':
        form=VolunteerForm(request.POST, request.FILES)
    elif user_type=='organization':
        form=OrganizationForm(request.POST, request.FILES)

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
        # Get user profile data
        user_profile = get_user_profile(request, account_uuid)
        if user_profile.status_code==404:
            context['message'] = 'Profile not found'
        else:
            context['user_profile'] = json.loads(user_profile.content)

        # Get whether logged-in user is following the profile user
        is_following = get_following(request, account_uuid)
        if is_following.status_code==404:
            context['message'] = 'Following not found'
        else:
            context['is_following'] = is_following.data

        # Get follower count of profile user
        followers = get_all_followers(request, account_uuid)
        if followers.status_code==404:
            context['message'] = 'Followers not found'
        else:
            context['followers_count'] = followers.data
    else:
        followers = get_all_followers(request, account_uuid)
        if followers.status_code==404:
            context['message'] = 'Followers not found'
        else:
            context['followers_count'] = followers.data
        
        # If the user is viewing their own profile, check if they are a volunteer and have not set their matching preferences
        show_preferences_modal = False
        if request.user.is_volunteer() and not VolunteerMatchingPreferences.objects.filter(volunteer=request.user.volunteer).exists():
            show_preferences_modal = True
            context['show_preferences_modal'] = show_preferences_modal

            # Dynamically pass the choices to the modal preferences template
            context["days_of_week"] = [choice[0] for choice in VolunteerMatchingPreferences.DAYS_OF_WEEK_CHOICES]
            context["work_types"] = [choice[0] for choice in VolunteerMatchingPreferences.WORK_TYPE_CHOICES]
            context["durations"] = [choice[0] for choice in VolunteerMatchingPreferences.DURATION_CHOICES]
            context["fields_of_interest"] = [choice[0] for choice in VolunteerMatchingPreferences.FIELDS_OF_INTEREST_CHOICES]
            context["skills"] = [choice[0] for choice in VolunteerMatchingPreferences.SKILLS_CHOICES]

        else:
            if request.session.get('show_preferences_modal'):
                request.session.pop('show_preferences_modal', None)

        
    
    status_posts = get_status_posts(request, account_uuid)
    if status_posts.status_code==404:
        context['message'] = 'Status posts not found'
    else:
        context['status_posts'] = status_posts.data

    endorsements = get_endorsements(request, account_uuid)
    if endorsements.status_code==404:
        context['message'] = 'Endorsements not found'
    else:
        context['endorsements'] = endorsements.data
    print(context)
    return render(request, 'volunteers_organizations/profile.html', context)

@login_required
def search_profiles_view(request):
    search_response = get_search_profiles(request)

    if search_response.status_code != 200:
        return render(request, 'volunteers_organizations/search_profiles.html', {'message': 'Profiles not found'})

    search_results = search_response.data.get("results", [])

    paginator = Paginator(search_results, 10)
    page_number = request.GET.get('page')
    paginated_results = paginator.get_page(page_number)

    return render(request, 'volunteers_organizations/search_profiles.html', {
        'results': paginated_results,
        'query': request.GET.get('q')
    })

@login_required
def update_profile_view(request):
    account = request.user

    if account.is_volunteer():
        instance = get_object_or_404(Volunteer, account=account)
        form_class = VolunteerForm
    elif account.is_organization():
        instance = get_object_or_404(Organization, account=account)
        form_class = OrganizationForm
    else:
        return redirect("volunteers_organizations:profile", account_uuid=account.account_uuid)
    
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("volunteers_organizations:profile", account_uuid=account.account_uuid)
    else:
        form = form_class(instance=instance)
    
    return render(request, "volunteers_organizations/update_profile.html", {
        "form": form,
        "user_type": account.user_type
    })
