from rest_framework import status
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts_notifs.models import Account
from volunteers_organizations.api import get_volunteer_preferences
from .api import get_organization_opportunities, get_opportunity
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
    return render(request, 'base/base_error.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

@login_required
def opportunities_organization_view(request):
    account = request.user
    context = {}

    if account.is_organization():
        # Fetch the organization's opportunities
        response = get_organization_opportunities(request)

        if response.status_code == 200:
            opportunities = response.data
        else:
            opportunities = []

        # Categorize opportunities for filtering
        context["upcoming_opportunities"] = [opp for opp in opportunities if opp["status"] == "upcoming"]
        context["completed_opportunities"] = [opp for opp in opportunities if opp["status"] == "completed"]
        context["cancelled_opportunities"] = [opp for opp in opportunities if opp["status"] == "cancelled"]
        context["all_opportunities"] = opportunities  # All available opportunities

        return render(request, 'opportunities_engagements/opportunities_organization.html', context)

    return render(request, 'base/base_error.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

@login_required
def opportunity_view(request, opportunity_id):
    account = request.user
    context = {}

    opportunity_response = get_opportunity(request, opportunity_id)

    if opportunity_response.status_code != 200:
        return render(request, 'base/base_error.html', {"status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    
    opportunity = opportunity_response.data
    context["opportunity"] = opportunity

    if account.is_organization():
        if opportunity['organization']['account_uuid'] == str(account.account_uuid):
            context["is_opportunity_owner"] = True
        else:
            return render(request, 'base/base_error.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
        
    if account.is_volunteer():
        context["is_opportunity_owner"] = False

        # Check if volunteer has applied to this opportunity
        applications_response = get_volunteer_applications(request, account.account_uuid)
        if applications_response.status_code == 200:
            applications = applications_response.data
            context["has_applied"] = any(app["volunteer_opportunity"]["volunteer_opportunity_id"] == opportunity_id 
                                         for app in applications)

        engagements_response = get_engagements(request, account.account_uuid)
        if engagements_response.status_code == 200:
            engagements = engagements_response.data
            context["is_engaged"] = any(eng["volunteer_opportunity_application"]["volunteer_opportunity"]["volunteer_opportunity_id"] == opportunity_id 
                                        for eng in engagements)
    
    if opportunity["ongoing"]:
        sessions_response = get_sessions(request, opportunity_id)
        if sessions_response.status_code == 200:
            context["sessions"] = sessions_response.data
        else:
            context["sessions"] = []

    return render(request, 'opportunities_engagements/opportunity.html', context)

# @login_required
# def engagements_application_view(request):