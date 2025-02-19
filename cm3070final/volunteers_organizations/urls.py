from django.urls import path
from .views import signup_final, profile_view

urlpatterns = [
    path('signup_final/', signup_final, name='signup_final'),
    path('profile/<uuid:account_uuid>', profile_view, name='profile'),
]