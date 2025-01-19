from django.urls import path
from .views import volunteer_signup, organization_signup

urlpatterns = [
    path('signup/volunteer/', volunteer_signup, name='volunteer_signup'),
    path('signup/organization/', organization_signup, name='organization_signup')
]