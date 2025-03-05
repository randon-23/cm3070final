from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts_notifs.models import Account
from volunteers_organizations.api import get_volunteer_preferences
import json
import pycountry
from .models import *
from .api import *

@login_required
def opportunities_search_view(request):
    account = request.user
    context = {}

    if account.is_volunteer():
        context["days_of_week"] = [choice[0] for choice in VolunteerOpportunity.DAYS_OF_WEEK_CHOICES]
        context["work_types"] = [choice[0] for choice in VolunteerOpportunity.WORK_BASIS_TYPES]
        context["durations"] = [choice[0] for choice in VolunteerOpportunity.DURATION_CHOICES]
        context["area_of_work"] = [choice[0] for choice in VolunteerOpportunity.FIELDS_OF_INTEREST_CHOICES]
        context["requirements"] = [choice[0] for choice in VolunteerOpportunity.SKILLS_CHOICES]
        languages = [(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')]
        context["languages"] = languages

        preferences = get_volunteer_preferences(request)
        if preferences.status_code != 200:
            context["message"] = "Preferences not found"
        else:
            context['preferences'] = preferences.data

        return render(request, 'opportunities_engagements/opportunities_search.html', context)

    # If user is an organization, return unauthorized page
    return render(request, 'base/base_unauthorized.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)