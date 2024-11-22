from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property, PropertyImage, Favorite

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'profile_picture')}),
    )

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'property_type', 'listing_type', 'price', 'city', 'is_available')
    list_filter = ('property_type', 'listing_type', 'is_available', 'city')
    search_fields = ('title', 'description', 'address', 'city', 'state', 'zip_code')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('property__title',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    search_fields = ('user__username', 'property__title')
    list_filter = ('created_at',)
