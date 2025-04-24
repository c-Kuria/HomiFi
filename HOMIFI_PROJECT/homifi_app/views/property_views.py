from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from ..models import Property, PropertyImage, Favorite, Inquiry
from ..forms import PropertyForm, PropertyImageFormSet

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
            user=request.user,
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        
        messages.success(request, 'Your inquiry has been sent to the property owner.')
        return redirect('homifi_app:property_detail', pk=pk) 