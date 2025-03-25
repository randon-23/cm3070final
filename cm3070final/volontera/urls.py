"""
URL configuration for volontera project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpRequest

def root_redirect_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect(f'/volunteers-organizations/profile/{request.user.account_uuid}')
    return redirect('/accounts/auth/?type=login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect_view),
    path('home/', lambda request: redirect('/')), # Redirect to home
    path('accounts/', include('accounts_notifs.urls')),
    path('volunteers-organizations/', include('volunteers_organizations.urls')),
    path('oauth/', include('allauth.urls')),
    path('opportunities-engagements/', include('opportunities_engagements.urls')),
    path('chats/', include('chats.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)