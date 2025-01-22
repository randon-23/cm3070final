from django.urls import path
from .views import account_signup, login_view
from .api import login_api

app_name = 'accounts_notifs'

urlpatterns = [
    path('signup/', account_signup, name='account_signup'),
    path('login/', login_view, name='login'),
    path('api/login/', login_api, name='login_api')
]