from rest_framework import serializers
from .models import Property, PropertyImage, User

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_primary']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'price', 'property_type',
            'listing_type', 'bedrooms', 'bathrooms', 'area',
            'address', 'city', 'state', 'zip_code',
            'latitude', 'longitude', 'is_available',
            'created_at', 'updated_at', 'owner', 'images'
        ]
        read_only_fields = ['created_at', 'updated_at', 'owner']