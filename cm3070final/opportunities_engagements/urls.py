from django.urls import path
from .views import opportunities_search_view
from .api import get_opportunities, get_nearby_opportunities, get_latest_opportunities, create_opportunity, get_organization_opportunities, cancel_opportunity, complete_opportunity, create_application, accept_application, reject_application, cancel_application, get_volunteer_applications, get_organization_applications, create_engagement, get_engagements, complete_engagements_organization, cancel_engagement_volunteer, cancel_engagements_organization, create_session, get_sessions, complete_session, cancel_session, create_session_engagements_for_session, create_session_engagements_for_volunteer, confirm_attendance, cancel_attendance, get_session_engagements, create_opportunity_engagement_logs, create_session_engagement_logs, create_engagement_log_volunteer, approve_engagement_log, reject_engagement_log

app_name = 'opportunities_engagements'

urlpatterns = [
    ### View endpoints ###
    path('opportunities_search/', opportunities_search_view, name='opportunities_search'),

    ### REST API Endpoints ###
    ### Opportunities ###
    path('api/opportunities/get_opportunities', get_opportunities, name='get_opportunities'),
    path('api/opportunities/get_nearby_opportunities', get_nearby_opportunities, name='get_nearby_opportunities'),
    path('api/opportunities/get_latest_opportunities', get_latest_opportunities, name='get_latest_opportunities'),
    path('api/opportunities/create_opportunity', create_opportunity, name='create_opportunity'),
    path('api/opportunities/get_organization_opportunities', get_organization_opportunities, name='get_organization_opportunities'),
    path('api/opportunities/cancel_opportunity/<uuid:volunteer_opportunity_id>', cancel_opportunity, name='cancel_opportunity'),
    path('api/opportunities/complete_opportunity/<uuid:volunteer_opportunity_id>', complete_opportunity, name='complete_opportunity'),

    ### Applications ###
    path('api/opportunities/applications/create/<uuid:volunteer_opportunity_id>', create_application, name='create_application'),
    path('api/opportunities/applications/accept/<uuid:application_id>/', accept_application, name='accept_application'),
    path('api/opportunities/applications/reject/<uuid:application_id>/', reject_application, name='reject_application'),
    path('api/opportunities/applications/cancel/<uuid:application_id>/', cancel_application, name='cancel_application'),
    path('api/opportunities/applications/volunteer/<uuid:account_uuid>/', get_volunteer_applications, name='get_volunteer_applications'),
    path('api/opportunities/applications/organization/<uuid:account_uuid>/', get_organization_applications, name='get_organization_applications'),
    
    ### Engagements ###
    path('api/engagements/create_engagement/<uuid:application_id>/', create_engagement, name='create_engagement'),
    path('api/engagements/get_engagements/<uuid:account_uuid>/', get_engagements, name='get_engagements'),
    path('api/engagements/complete_engagements_organization/<uuid:volunteer_opportunity_id>/', complete_engagements_organization, name='complete_engagements_organization'),
    path('api/engagements/cancel_engagement_volunteer/<uuid:volunteer_engagement_id>/', cancel_engagement_volunteer, name='cancel_engagement_volunteer'),
    path('api/engagements/cancel_engagements_organization/<uuid:volunteer_opportunity_id>/', cancel_engagements_organization, name='cancel_engagements_organization'),
    
    ### Sessions ###
    path('api/sessions/create_session/<uuid:opportunity_id>/', create_session, name='create_session'),
    path('api/sessions/get_sessions/<uuid:opportunity_id>/', get_sessions, name='get_sessions'),
    path('api/complete_session/<uuid:session_id>/', complete_session, name='complete_session'),
    path('api/cancel_session/<uuid:session_id>/', cancel_session, name='cancel_session'),

    ### Session Engagements ###
    path('api/sessions/create_session_engagements_for_session/<uuid:session_id>/', create_session_engagements_for_session, name='create_session_engagements_for_session'),
    path('api/sessions/create_session_engagements_for_volunteer/<uuid:account_uuid>/', create_session_engagements_for_volunteer, name='create_session_engagements_for_volunteer'),
    path('api/sessions/confirm_attendance/<uuid:session_engagement_id>/', confirm_attendance, name='confirm_attendance'),
    path('api/sessions/cancel_attendance/<uuid:session_engagement_id>/', cancel_attendance, name='cancel_attendance'),
    path('api/sessions/get_session_engagements/<uuid:session_id>/', get_session_engagements, name='get_session_engagements'),

    ### Engagement Logs
    path('api/engagement_logs/create_opportunity_engagement_logs/<uuid:opportunity_id>', create_opportunity_engagement_logs, name='create_opportunity_engagement_logs'),
    path('api/engagement_logs/create_session_engagement_logs/<uuid:session_id>', create_session_engagement_logs, name='create_session_engagement_logs'),
    path('api/engagement_logs/create_engagement_log_volunteer/<uuid:opportunity_id>', create_engagement_log_volunteer, name='create_engagement_log_volunteer'),
    path('api/engagement_logs/approve_engagement_log/<uuid:volunteer_engagement_log_id>', approve_engagement_log, name='approve_engagement_log'),
    path('api/engagement_logs/reject_engagement_log/<uuid:volunteer_engagement_log_id>', reject_engagement_log, name='reject_engagement_log'),
]