from django.urls import path
from .views import signup_final, profile_view, search_profiles_view, update_profile_view, preferences_view
from .api import get_user_profile, get_all_followers, get_following, create_following, delete_following, get_endorsements, create_endorsement, delete_endorsement, get_status_posts, create_status_post, delete_status_post, get_search_profiles, create_volunteer_preferences

app_name = 'volunteers_organizations'

urlpatterns = [
    # View endpoints
    path('signup_final/', signup_final, name='signup_final'),
    path('profile/<uuid:account_uuid>', profile_view, name='profile'),
    path('search_profiles/', search_profiles_view, name='search_profiles'),
    path('update_profile/', update_profile_view, name='update_profile'),
    path('preferences/<uuid:account_uuid>', preferences_view, name='preferences'),

    ### REST API Endpoints ###
    # Account profile endpoints
    path('api/profile/<uuid:account_uuid>', get_user_profile, name='get_user_profile'),
    # Following endpoints
    path('api/following/get_all_followers/<uuid:account_uuid>', get_all_followers, name='get_all_followers'),
    path('api/following/get_following/<uuid:account_uuid>', get_following, name='get_following'),
    path('api/following/create_following/<uuid:account_uuid>', create_following, name='create_following'),
    path('api/following/delete_following/<uuid:account_uuid>', delete_following, name='delete_following'),
    # Endorsement endpoints
    path('api/endorsements/get_endorsements/<uuid:account_uuid>', get_endorsements, name='get_endorsements'),
    path("api/endorsements/create_endorsement/<uuid:account_uuid>/", create_endorsement, name="create_endorsement"),
    path("api/endorsements/delete_endorsement/<uuid:id>/", delete_endorsement, name="delete_endorsement"),
    # Status post endpoints
    path("api/status_posts/get_status_posts/<uuid:account_uuid>/", get_status_posts, name="get_status_posts"),
    path("api/status/create_status_post/", create_status_post, name="create_status_post"),
    path("api/status/delete_status_post/<uuid:id>/", delete_status_post, name="delete_status_post"),
    # Search profiles endpoints
    path("api/search/get_search_profiles/", get_search_profiles, name="get_search_profiles"),
    #Volunteer Matching Preferences
    path('api/volunteer_matching_preferences/create_volunteer_preferences/', create_volunteer_preferences, name='create_volunteer_preferences'),
]