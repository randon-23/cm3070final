from rest_framework import status
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts_notifs.models import Account
from volunteers_organizations.api import get_volunteer_preferences
from .api import get_organization_opportunities, get_opportunity, get_volunteer_applications, get_engagements, get_sessions, get_organization_applications, get_organization_log_requests, get_volunteer_session_engagements
from volunteers_organizations.api import get_organization_preferences
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

        nearby_response = get_nearby_opportunities(request)
        context["nearby_opportunities"] = nearby_response.data if nearby_response.status_code == 200 else []

        latest_response = get_latest_opportunities(request)
        context["latest_opportunities"] = latest_response.data if latest_response.status_code == 200 else []

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

        preferences = get_organization_preferences(request)
        if preferences.status_code != 200:
            context["message"] = "Preferences not found"
        else:
            context['preferences'] = preferences.data

        # Passes choices to dynamically populate create opportunity form
        context["days_of_week"] = [choice[0] for choice in VolunteerOpportunity.DAYS_OF_WEEK_CHOICES]
        context["work_types"] = [choice[0] for choice in VolunteerOpportunity.WORK_BASIS_TYPES]
        context["durations"] = [choice[0] for choice in VolunteerOpportunity.DURATION_CHOICES]
        context["area_of_work"] = [choice[0] for choice in VolunteerOpportunity.FIELDS_OF_INTEREST_CHOICES]
        context["requirements"] = [choice[0] for choice in VolunteerOpportunity.SKILLS_CHOICES]
        languages = [(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')]
        context["languages"] = languages

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
    context["organization"] = opportunity["organization"]

    is_owner = account.is_organization() and opportunity['organization']['account_uuid'] == str(account.account_uuid)
    context["is_opportunity_owner"] = is_owner

    if account.is_organization() and not is_owner:
        return render(request, 'base/base_error.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
        
    if account.is_volunteer():
        context["is_opportunity_owner"] = False
        context["has_applied"] = False
        context["is_engaged"] = False
        context["is_rejected"] = False

        # Check if volunteer has applied to this opportunity, and if they have been rejected
        applications_response = get_volunteer_applications(request, account.account_uuid)
        if applications_response.status_code == 200:
            applications = applications_response.data
            for app in applications:
                if app["volunteer_opportunity"]["volunteer_opportunity_id"] == opportunity_id:
                    context["has_applied"] = True
                    context["is_rejected"] = app["application_status"] == "rejected"
                    break
        
        # Check if volunteer is engaged in this opportunity
        engagements_response = get_engagements(request, account.account_uuid)
        if engagements_response.status_code == 200:
            engagements = engagements_response.data
            context["is_engaged"] = any(
                eng["volunteer_opportunity_application"]["volunteer_opportunity"]["volunteer_opportunity_id"] == opportunity_id
                and eng["engagement_status"] == "accepted"
                for eng in engagements
            )
    
    if opportunity["ongoing"]:
        sessions_response = get_sessions(request, opportunity_id)
        if sessions_response.status_code == 200:
            sessions = sessions_response.data

            # Only fetch session engagements if the account is a volunteer
            if account.is_volunteer():
                session_engagements_response = get_volunteer_session_engagements(request, account.account_uuid)
                session_engagements = session_engagements_response.data if session_engagements_response.status_code == 200 else []

                # Attach session engagement ID to each session
                for session in sessions:
                    session["session_engagement_id"] = None
                    for eng in session_engagements:
                        if eng["session"]["session_id"] == session["session_id"]:
                            session["session_engagement_id"] = eng["session_engagement_id"]
                            session["status"] = eng["status"]  # Store engagement status for UI
                            break
            
            # If user is not the owner, only show confirmed sessions
            if not is_owner:
                sessions = [s for s in sessions if s["status"] == "upcoming"]
            
            context["sessions"] = sessions
        else:
            context["sessions"] = []

    return render(request, 'opportunities_engagements/opportunity.html', context)

@login_required
def engagements_applications_log_requests_view(request):
    account = request.user
    context = {}

    if account.is_volunteer():
        engagements_response = get_engagements(request, account.account_uuid)
        if engagements_response.status_code == 200:
            engagements = engagements_response.data
            context["engagements"] = engagements
            # Categorizing for filtering
            context["ongoing_engagements"] = [e for e in engagements if e["engagement_status"] == "ongoing"]
            context["completed_engagements"] = [e for e in engagements if e["engagement_status"] == "completed"]
            context["cancelled_engagements"] = [e for e in engagements if e["engagement_status"] == "cancelled"]
        else:
            context["engagements"] = []
            context["ongoing_engagements"] = []
            context["completed_engagements"] = []
            context["cancelled_engagements"] = []

        applications_response = get_volunteer_applications(request, account.account_uuid)
        if applications_response.status_code == 200:
            applications = applications_response.data
            context["applications"] = applications
            # Categorizing for filtering
            context["pending_applications"] = [a for a in applications if a["application_status"] == "pending"]
            context["accepted_applications"] = [a for a in applications if a["application_status"] == "accepted"]
            context["rejected_applications"] = [a for a in applications if a["application_status"] == "rejected"]
            context["cancelled_applications"] = [a for a in applications if a["application_status"] == "cancelled"]
        else:
            context["applications"] = []
            context["pending_applications"] = []
            context["accepted_applications"] = []
            context["rejected_applications"] = []
            context["cancelled_applications"] = []
        
        # Fetch log requests (only volunteer-submitted ones)
        log_requests_response = get_volunteer_log_requests(request, account.account_uuid)
        if log_requests_response.status_code == 200:
            log_requests = log_requests_response.data
            context["log_requests"] = log_requests
            context["pending_log_requests"] = [l for l in log_requests if l["status"] == "pending"]
            context["approved_log_requests"] = [l for l in log_requests if l["status"] == "approved"]
            context["rejected_log_requests"] = [l for l in log_requests if l["status"] == "rejected"]
        else:
            context["log_requests"] = []
            context["pending_log_requests"] = []
            context["approved_log_requests"] = []
            context["rejected_log_requests"] = []
        
        return render(request, 'opportunities_engagements/engagements_applications_log_requests.html', context)
    
    return render(request, 'base/base_error.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

@login_required
def applications_log_requests_view(request):
    account = request.user
    context = {}

    if account.is_organization():
        applications_response = get_organization_applications(request, account.account_uuid)
        if applications_response.status_code == 200:
            applications = applications_response.data
            # Only pending applicaions and log requests are shown in this view
            context["applications"] = [a for a in applications if a["application_status"] == "pending"]
        else:
            context["applications"] = []

        # Fetch pending engagement log requests
        log_requests_response = get_organization_log_requests(request, account.account_uuid)
        if log_requests_response.status_code == 200:
            log_requests = log_requests_response.data
            # Only pending log_requests shown in this view
            context["log_requests"] = [l for l in log_requests if l["status"] == "pending"]
        else:
            context["log_requests"] = []
        
        return render(request, 'opportunities_engagements/applications_log_requests.html', context)
    return render(request, 'base/base_error.html', {"status_code": status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

