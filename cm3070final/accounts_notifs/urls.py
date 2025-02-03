from django.urls import path
from .views import authentication_view
from .api import login_api, logout_api

app_name = 'accounts_notifs'

urlpatterns = [
    path('auth/', authentication_view, name='authentication'),
    path('api/login/', login_api, name='login'),
    path('api/logout/', logout_api, name='logout'),
]