from django.conf import settings

def google_maps_api_key(request):
    """
    Makes Google Maps API key available to all templates
    """
    return {'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY}