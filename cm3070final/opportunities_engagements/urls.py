from django.urls import path
from .views import opportunities_search_view
from .api import get_opportunities

app_name = 'opportunities_engagements'

urlpatterns = [
    ### View endpoints ###
    path('opportunities_search/', opportunities_search_view, name='opportunities_search'),

    ### REST API Endpoints ###
    path('api/opportunities/get_opportunities', get_opportunities, name='get_opportunities'),
]