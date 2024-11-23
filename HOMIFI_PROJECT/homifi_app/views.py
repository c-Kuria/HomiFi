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
from django.contrib.auth import login
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Property, PropertyImage, SavedSearch, Favorite, User
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
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('homifi_app:index')
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

class PropertyCreateView(LoginRequiredMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    success_url = reverse_lazy('property_list')

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
        form.instance.owner = self.request.user
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            response = super().form_valid(form)
            image_formset.instance = self.object
            image_formset.save()
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    success_url = reverse_lazy('property_list')

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
    success_url = reverse_lazy('property_list')
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

@login_required
def dashboard(request):
    user_properties = Property.objects.filter(owner=request.user)
    return render(request, 'dashboard/dashboard.html', {
        'properties': user_properties
    })

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
