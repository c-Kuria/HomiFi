from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.validators import MinValueValidator
from .models import User, Property, PropertyImage
from django.contrib.auth import authenticate

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    profile_picture = forms.ImageField(required=False)
    role = forms.ChoiceField(choices=User.USER_ROLES, required=True)
    location = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 
                 'phone_number', 'profile_picture', 'location']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean_username(self):
        # Remove username uniqueness validation
        return self.cleaned_data.get('username')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('role'):
            raise forms.ValidationError('Please select a role (Renter or Landlord)')
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (123) 456-7890'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'phone_number': 'Enter your phone number in international format',
            'profile_picture': 'Upload a square image for best results. Maximum size: 5MB'
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email
    
    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image file size must be less than 5MB.')
            if not profile_picture.content_type.startswith('image'):
                raise forms.ValidationError('File must be an image.')
        return profile_picture

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
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

PropertyImageFormSet = forms.inlineformset_factory(
    Property,
    PropertyImage,
    form=PropertyImageForm,
    extra=1,
    can_delete=True,
    max_num=10,
    validate_max=True,
    fields=['image', 'is_primary']
)

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    def clean(self):
        email = self.cleaned_data.get('username')  # Django's auth form uses 'username' field
        password = self.cleaned_data.get('password')

        if email is not None and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Please enter a correct email and password. Note that both fields are case-sensitive.",
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

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