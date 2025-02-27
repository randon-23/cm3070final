from django.conf import settings

# Adds the Google Places API key to the context
def google_places_api_key(request):
    return {
        'GOOGLE_PLACES_API_KEY': settings.GOOGLE_PLACES_API_KEY
    }