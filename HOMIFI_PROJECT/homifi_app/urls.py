from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import UserLoginForm

app_name = 'homifi_app'

urlpatterns = [
    # Base URLs
    path('', views.index, name='index'),
    
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        form_class=UserLoginForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='homifi_app:index'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Password Reset URLs
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset_form.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Property URLs
    path('properties/', views.PropertyListView.as_view(), name='property_list'),
    path('properties/create/', views.PropertyCreateView.as_view(), name='property_create'),
    path('properties/<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('properties/<int:pk>/edit/', views.PropertyUpdateView.as_view(), name='property_edit'),
    path('properties/<int:pk>/delete/', views.PropertyDeleteView.as_view(), name='property_delete'),
    path('properties/<int:pk>/contact/', views.ContactOwnerView.as_view(), name='contact_owner'),
    
    # Property Images
    path('api/property-images/<int:pk>/', views.PropertyImageDeleteView.as_view(), name='property_image_delete'),
    
    # API Endpoints
    path('api/properties/', views.PropertyAPIView.as_view(), name='property_api_list'),
    path('api/properties/<int:pk>/', views.PropertyDetailAPIView.as_view(), name='property_api_detail'),
    
    # Inquiry URLs
    path('inquiries/<int:pk>/detail/', views.inquiry_detail_view, name='inquiry_detail'),
    
    # Account Management URLs
    path('accounts/create-linked/', views.create_linked_account, name='create_linked_account'),
    path('accounts/switch/<int:account_id>/', views.switch_account, name='switch_account'),
    path('accounts/manage/', views.manage_accounts, name='manage_accounts'),
]