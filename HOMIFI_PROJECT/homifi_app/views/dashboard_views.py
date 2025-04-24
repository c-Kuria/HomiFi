from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Property, Inquiry, Favorite

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
def inquiry_detail_view(request, pk):
    inquiry = Inquiry.objects.select_related('property', 'user').get(pk=pk)
    
    # Check if user has permission to view this inquiry
    if request.user.role == 'landlord':
        if inquiry.property.owner != request.user:
            messages.error(request, 'You do not have permission to view this inquiry.')
            return redirect('homifi_app:dashboard')
    else:
        if inquiry.user != request.user:
            messages.error(request, 'You do not have permission to view this inquiry.')
            return redirect('homifi_app:dashboard')
    
    # Mark as read if it's unread
    if not inquiry.is_read:
        inquiry.is_read = True
        inquiry.save()
    
    return render(request, 'dashboard/inquiry_detail.html', {
        'inquiry': inquiry,
        'page_title': 'Inquiry Details'
    }) 