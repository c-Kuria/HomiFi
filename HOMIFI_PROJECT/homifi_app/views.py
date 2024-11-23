from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth import login, logout
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Property, PropertyImage, SavedSearch, Favorite, User, Inquiry, LinkedAccount
from .forms import PropertyForm, PropertyImageFormSet, UserRegistrationForm, UserProfileForm
from .serializers import PropertySerializer
import requests
from math import radians, sin, cos, sqrt, atan2
import json
from django.contrib import messages

def index(request):
    featured_properties = Property.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'index.html', {'featured_properties': featured_properties})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('homifi_app:index')
            except Exception as e:
                form.add_error(None, str(e))
        else:
            pass
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

class PropertyListView(ListView):
    model = Property
    template_name = 'properties/property_list.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        queryset = Property.objects.filter(is_available=True)
        
        # Apply search filters if provided
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')

class PropertyDetailView(DetailView):
    model = Property
    template_name = 'properties/property_detail.html'
    context_object_name = 'property'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user,
                property=self.object
            ).exists()
        return context

class PropertyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    success_url = reverse_lazy('homifi_app:dashboard')

    def test_func(self):
        return self.request.user.role == 'landlord'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = PropertyImageFormSet(
                self.request.POST,
                self.request.FILES
            )
        else:
            context['image_formset'] = PropertyImageFormSet()
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        return context

    def form_valid(self, form):
        try:
            form.instance.owner = self.request.user
            context = self.get_context_data()
            image_formset = context['image_formset']
            
            if image_formset.is_valid():
                self.object = form.save()
                image_formset.instance = self.object
                image_formset.save()
                messages.success(self.request, 'Property created successfully!')
                return redirect(self.success_url)
            else:
                messages.error(self.request, 'Please correct the errors in the image upload form.')
                return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error creating property: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def handle_no_permission(self):
        messages.error(self.request, 'Only landlords can create properties.')
        return redirect('homifi_app:index')

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    success_url = reverse_lazy('homifi_app:dashboard')

    def test_func(self):
        property = self.get_object()
        return self.request.user == property.owner

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = PropertyImageFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object
            )
        else:
            context['image_formset'] = PropertyImageFormSet(instance=self.object)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            response = super().form_valid(form)
            image_formset.save()
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

class PropertyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Property
    success_url = reverse_lazy('homifi_app:dashboard')
    template_name = 'properties/property_confirm_delete.html'

    def test_func(self):
        property = self.get_object()
        return self.request.user == property.owner

class PropertyImageDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        image = get_object_or_404(PropertyImage, pk=pk)
        if request.user == image.property.owner:
            image.delete()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'}, status=403)

class ContactOwnerView(LoginRequiredMixin, View):
    def post(self, request, pk):
        property = get_object_or_404(Property, pk=pk)
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        # Create inquiry
        Inquiry.objects.create(
            property=property,
            inquirer=request.user,
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        
        messages.success(request, 'Your inquiry has been sent to the property owner.')
        return redirect('homifi_app:property_detail', pk=pk)

@login_required
def dashboard(request):
    context = {}
    
    if request.user.role == 'landlord':
        # Landlord-specific data
        properties = Property.objects.filter(owner=request.user)
        inquiries = Inquiry.objects.filter(property__owner=request.user).select_related('property', 'user')
        
        context.update({
            'properties': properties,
            'properties_count': properties.count(),
            'active_listings': properties.filter(is_available=True).count(),
            'total_views': sum(p.view_count for p in properties) if hasattr(Property, 'view_count') else 0,
            'inquiries': inquiries,
            'inquiries_count': inquiries.count(),
            'page_title': 'Landlord Dashboard',
        })
    else:
        # Buyer-specific data
        favorites = Favorite.objects.filter(user=request.user).select_related('property')
        inquiries = Inquiry.objects.filter(user=request.user).select_related('property')
        
        context.update({
            'favorites': favorites,
            'favorites_count': favorites.count(),
            'recent_views': request.user.property_views.count() if hasattr(request.user, 'property_views') else 0,
            'inquiries': inquiries,
            'sent_inquiries': inquiries.count(),
            'page_title': 'Buyer Dashboard',
        })
    
    messages.info(request, f'Welcome to your {context["page_title"]}!')
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Handle profile picture removal
            if request.POST.get('remove_picture') == 'true' and request.user.profile_picture:
                # Delete the old file
                request.user.profile_picture.delete(save=False)
                # Clear the field
                request.user.profile_picture = None
            
            user = form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('homifi_app:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'auth/profile.html', {
        'form': form,
        'page_title': 'Edit Profile',
    })

@login_required
def create_linked_account(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create new user account
            new_user = form.save()
            
            # Create linked account relationship
            LinkedAccount.objects.create(
                primary_user=request.user,
                secondary_user=new_user
            )
            
            messages.success(request, 'Secondary account created successfully!')
            return redirect('homifi_app:profile')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/create_linked_account.html', {'form': form})

@login_required
def switch_account(request, account_id):
    try:
        # Find the linked account
        linked_account = LinkedAccount.objects.get(
            Q(primary_user=request.user, secondary_user_id=account_id) |
            Q(secondary_user=request.user, primary_user_id=account_id)
        )
        
        # Get the account to switch to
        switch_to_user = linked_account.secondary_user if linked_account.primary_user == request.user else linked_account.primary_user
        
        # Log out current user
        logout(request)
        
        # Log in as the other user
        login(request, switch_to_user)
        messages.success(request, f'Switched to account: {switch_to_user.username}')
        
    except LinkedAccount.DoesNotExist:
        messages.error(request, 'Invalid account switch request.')
    
    return redirect('homifi_app:index')

@login_required
def manage_accounts(request):
    # Get all linked accounts where user is either primary or secondary
    linked_accounts = LinkedAccount.objects.filter(
        Q(primary_user=request.user) |
        Q(secondary_user=request.user)
    ).select_related('primary_user', 'secondary_user')
    
    return render(request, 'auth/manage_accounts.html', {
        'linked_accounts': linked_accounts
    })

@login_required
def inquiry_detail_view(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    
    # Check if user has permission to view this inquiry
    if request.user != inquiry.user and request.user != inquiry.property.owner:
        messages.error(request, "You don't have permission to view this inquiry.")
        return redirect('homifi_app:dashboard')
    
    # Mark inquiry as read if viewing as property owner
    if request.user == inquiry.property.owner and not inquiry.is_read:
        inquiry.is_read = True
        inquiry.save()
    
    context = {
        'inquiry': inquiry,
        'property': inquiry.property,
        'is_owner': request.user == inquiry.property.owner,
    }
    
    return render(request, 'enquiries/enquiry_detail.html', context)

# API Views
class PropertyAPIView(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Property.objects.all()
        if self.request.query_params:
            filters = Q()
            
            # Price range
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            if min_price:
                filters &= Q(price__gte=float(min_price))
            if max_price:
                filters &= Q(price__lte=float(max_price))
            
            # Property type
            property_type = self.request.query_params.get('property_type')
            if property_type:
                filters &= Q(property_type=property_type)
            
            # Location
            city = self.request.query_params.get('city')
            state = self.request.query_params.get('state')
            if city:
                filters &= Q(city__icontains=city)
            if state:
                filters &= Q(state__icontains=state)
            
            queryset = queryset.filter(filters)
        
        return queryset.select_related('owner').prefetch_related('images')

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
