from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from math import cos, radians

class User(AbstractUser):
    USER_ROLES = [
        ('buyer', 'Buyer/Viewer'),
        ('landlord', 'Renter/Landlord'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='buyer')
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class Property(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('land', 'Land'),
        ('commercial', 'Commercial'),
    ]
    
    LISTING_TYPES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES)
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    area = models.PositiveIntegerField(help_text="Area in square feet")
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.property.title}"

    class Meta:
        ordering = ['-is_primary', '-created_at']

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')

    def __str__(self):
        return f"{self.user.username}'s favorite: {self.property.title}"

class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    query = models.CharField(max_length=255)
    filters = models.JSONField()
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_enabled = models.BooleanField(default=False)
    last_notification_sent = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s search: {self.query}"

    def get_matching_properties(self):
        """Get properties matching the saved search criteria"""
        filters = Q()
        
        if self.query:
            filters &= (
                Q(title__icontains=self.query) |
                Q(description__icontains=self.query) |
                Q(address__icontains=self.query)
            )
        
        for key, value in self.filters.items():
            if value:
                if key == 'min_price':
                    filters &= Q(price__gte=value)
                elif key == 'max_price':
                    filters &= Q(price__lte=value)
                elif key in ['property_type', 'listing_type', 'bedrooms', 'bathrooms']:
                    filters &= Q(**{key: value})
        
        if self.latitude and self.longitude:
            # Calculate properties within 50km radius
            radius = 50
            lat_range = radius / 111.0
            lng_range = radius / (111.0 * cos(radians(float(self.latitude))))
            
            filters &= Q(
                latitude__range=(float(self.latitude) - lat_range, float(self.latitude) + lat_range),
                longitude__range=(float(self.longitude) - lng_range, float(self.longitude) + lng_range)
            )
        
        return Property.objects.filter(filters)

    def send_notification(self):
        """Send notification if new matching properties are found"""
        if not self.notification_enabled:
            return
        
        # Get properties added since last notification
        new_properties = self.get_matching_properties().filter(
            created_at__gt=self.last_notification_sent or self.created_at
        )
        
        if new_properties.exists():
            # Prepare email content
            subject = 'New Properties Matching Your Search'
            message = f'Hello {self.user.username},\n\n'
            message += f'We found {new_properties.count()} new properties matching your saved search:\n\n'
            
            for prop in new_properties[:5]:  # Limit to 5 properties in email
                message += f'- {prop.title} - ${prop.price}\n'
            
            if new_properties.count() > 5:
                message += f'\nAnd {new_properties.count() - 5} more...\n'
            
            message += f'\nVisit HomiFi to view all properties: http://localhost:8000/properties/'
            
            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                fail_silently=True,
            )
            
            # Update last notification time
            self.last_notification_sent = timezone.now()
            self.save()
