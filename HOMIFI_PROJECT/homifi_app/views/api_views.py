from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from ..models import Property
from ..serializers import PropertySerializer

class PropertyAPIView(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Property.objects.filter(is_available=True)
        
        # Apply search filters
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        # Apply property type filter
        property_type = self.request.query_params.get('property_type', None)
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        # Apply price range filter
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Apply bedrooms filter
        bedrooms = self.request.query_params.get('bedrooms', None)
        if bedrooms:
            queryset = queryset.filter(bedrooms=bedrooms)
        
        # Apply bathrooms filter
        bathrooms = self.request.query_params.get('bathrooms', None)
        if bathrooms:
            queryset = queryset.filter(bathrooms=bathrooms)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class PropertyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Property.objects.select_related('owner').prefetch_related('images')
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)

    def test_func(self):
        property = self.get_object()
        return self.request.user == property.owner 