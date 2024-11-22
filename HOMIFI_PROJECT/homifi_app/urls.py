from django.urls import path
from . import views

app_name = 'homifi_app'

urlpatterns = [
    # Base URLs
    path('', views.index, name='index'),
    
    # Property URLs
    path('properties/', views.PropertyListView.as_view(), name='property_list'),
    path('properties/create/', views.PropertyCreateView.as_view(), name='property_create'),
    path('properties/<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('properties/<int:pk>/edit/', views.PropertyUpdateView.as_view(), name='property_edit'),
    path('properties/<int:pk>/delete/', views.PropertyDeleteView.as_view(), name='property_delete'),
    
    # Property Images
    path('api/property-images/<int:pk>/', views.PropertyImageDeleteView.as_view(), name='property_image_delete'),
    
    # API Endpoints
    path('api/properties/', views.PropertyAPIView.as_view(), name='property_api'),
    path('api/properties/<int:pk>/', views.PropertyDetailAPIView.as_view(), name='property_detail_api'),
]