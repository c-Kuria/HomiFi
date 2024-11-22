from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MinValueValidator
from .models import User, Property, PropertyImage

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    profile_picture = forms.ImageField(required=False)
    role = forms.ChoiceField(choices=User.USER_ROLES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 
                 'phone_number', 'profile_picture']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'profile_picture']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'price', 'property_type', 
            'listing_type', 'bedrooms', 'bathrooms', 'area',
            'address', 'city', 'state', 'zip_code',
            'latitude', 'longitude'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.NumberInput(attrs={'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'step': 'any'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        listing_type = cleaned_data.get('listing_type')
        property_type = cleaned_data.get('property_type')
        
        # Validate price is positive
        price = cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than zero")
            
        # Validate area is positive
        area = cleaned_data.get('area')
        if area and area <= 0:
            raise forms.ValidationError("Area must be greater than zero")
            
        # Validate coordinates if provided
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if latitude and (latitude < -90 or latitude > 90):
            raise forms.ValidationError("Latitude must be between -90 and 90 degrees")
        if longitude and (longitude < -180 or longitude > 180):
            raise forms.ValidationError("Longitude must be between -180 and 180 degrees")
            
        return cleaned_data

class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image', 'is_primary']
        widgets = {
            'is_primary': forms.CheckboxInput(),
        }

PropertyImageFormSet = forms.inlineformset_factory(
    Property,
    PropertyImage,
    form=PropertyImageForm,
    extra=1,
    can_delete=True,
    max_num=10
)

class PropertySearchForm(forms.Form):
    query = forms.CharField(required=False)
    property_type = forms.ChoiceField(
        choices=[('', 'All')] + Property.PROPERTY_TYPES,
        required=False
    )
    listing_type = forms.ChoiceField(
        choices=[('', 'All')] + Property.LISTING_TYPES,
        required=False
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    bedrooms = forms.IntegerField(required=False, min_value=0)
    bathrooms = forms.DecimalField(required=False, min_value=0)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError('Minimum price cannot be greater than maximum price.')