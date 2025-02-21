from django.urls import path
from .views import signup_final, profile_view
from .api import get_user_profile, get_all_followers, get_following, create_following, delete_following

app_name = 'volunteers_organizations'

urlpatterns = [
    # View endpoints
    path('signup_final/', signup_final, name='signup_final'),
    path('profile/<uuid:account_uuid>', profile_view, name='profile'),

    # REST API Endpoints
    path('api/profile/<uuid:account_uuid>', get_user_profile, name='get_user_profile'),
    path('api/following/get_all_followers/<uuid:account_uuid>', get_all_followers, name='get_all_followers'),
    path('api/following/get_following/<uuid:account_uuid>', get_following, name='get_following'),
    path('api/following/create_following/<uuid:account_uuid>', create_following, name='create_following'),
    path('api/following/delete_following/<uuid:account_uuid>', delete_following, name='delete_following')
]