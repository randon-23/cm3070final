from django.urls import path
from .views import signup_final

urlpatterns = [
    path('signup_final/', signup_final, name='signup_final'),
]