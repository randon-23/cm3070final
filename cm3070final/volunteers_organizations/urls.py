from django.urls import path
from .views import signup_final, profile_view
from .api import get_user_profile

app_name = 'volunteers_organizations'

urlpatterns = [
    # View endpoints
    path('signup_final/', signup_final, name='signup_final'),
    path('profile/<uuid:account_uuid>', profile_view, name='profile'),

    # REST API Endpoints
    path('api/profile/<uuid:account_uuid>', get_user_profile, name='get_user_profile'),
]