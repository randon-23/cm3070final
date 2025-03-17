from django.urls import path
from . import views
from . import api

app_name = 'accounts_notifs'

urlpatterns = [
    path('auth/', views.authentication_view, name='authentication'),
    path('api/login/', api.login_api, name='login'),
    path('api/logout/', api.logout_api, name='logout'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('api/password_reset_request', api.PasswordResetRequestEndpoint.as_view(), name='password_reset_request'),
    path('api/password_reset_confirm', api.PasswordResetConfirmEndpoint.as_view(), name='password_reset_confirm'),
    path('api/notifications/get_notifications/<uuid:account_uuid>', api.get_notifications, name='get_notifications'),
    path('api/notifications/mark_read/<uuid:notification_uuid>', api.mark_read, name='mark_read'),
    path('notifications/', views.notifications_view, name='notifications'),
]