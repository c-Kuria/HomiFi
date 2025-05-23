from django.shortcuts import render
from .models import Property
from .views import (
    PropertyListView,
    PropertyDetailView,
    PropertyCreateView,
    PropertyUpdateView,
    PropertyDeleteView,
    PropertyImageDeleteView,
    ContactOwnerView,
    register,
    profile,
    create_linked_account,
    switch_account,
    manage_accounts,
    PropertyAPIView,
    PropertyDetailAPIView,
    dashboard,
    inquiry_detail_view,
    index,
)

def index(request):
    featured_properties = Property.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'index.html', {'featured_properties': featured_properties})
