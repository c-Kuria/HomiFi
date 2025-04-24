from django.shortcuts import render
from ..models import Property

def index(request):
    featured_properties = Property.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'index.html', {'featured_properties': featured_properties}) 