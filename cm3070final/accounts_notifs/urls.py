from django.urls import path
from .views import authentication_view
from .api import login_api

app_name = 'accounts_notifs'

urlpatterns = [
    path('auth/', authentication_view, name='authentication'),
    path('api/login/', login_api, name='login_api')
]