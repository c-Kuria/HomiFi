from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Property, PropertyImage, Inquiry, Favorite

User = get_user_model()

class PropertyViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='landlord'
        )
        self.property = Property.objects.create(
            title='Test Property',
            description='Test Description',
            price=100000,
            property_type='house',
            listing_type='sale',
            bedrooms=3,
            bathrooms=2.0,
            area=1500,
            address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            owner=self.user
        )

    def test_property_list_view(self):
        response = self.client.get(reverse('homifi_app:property_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'properties/property_list.html')
        self.assertContains(response, 'Test Property')

    def test_property_detail_view(self):
        response = self.client.get(reverse('homifi_app:property_detail', args=[self.property.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'properties/property_detail.html')
        self.assertContains(response, 'Test Property')

    def test_property_create_view_authenticated(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('homifi_app:property_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'properties/property_form.html')

    def test_property_create_view_unauthenticated(self):
        response = self.client.get(reverse('homifi_app:property_create'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='landlord'
        )

    def test_register_view(self):
        response = self.client.get(reverse('homifi_app:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/register.html')

    def test_profile_view_authenticated(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('homifi_app:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/profile.html')

    def test_profile_view_unauthenticated(self):
        response = self.client.get(reverse('homifi_app:profile'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

class DashboardViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='landlord'
        )
        self.property = Property.objects.create(
            title='Test Property',
            description='Test Description',
            price=100000,
            property_type='house',
            listing_type='sale',
            bedrooms=3,
            bathrooms=2.0,
            area=1500,
            address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            owner=self.user
        )

    def test_dashboard_view_authenticated(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('homifi_app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')
        self.assertContains(response, 'Landlord Dashboard')

    def test_dashboard_view_unauthenticated(self):
        response = self.client.get(reverse('homifi_app:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

class APIViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='landlord'
        )
        self.property = Property.objects.create(
            title='Test Property',
            description='Test Description',
            price=100000,
            property_type='house',
            listing_type='sale',
            bedrooms=3,
            bathrooms=2.0,
            area=1500,
            address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            owner=self.user
        )

    def test_property_api_list_view_authenticated(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('homifi_app:property_api_list'))
        self.assertEqual(response.status_code, 200)

    def test_property_api_list_view_unauthenticated(self):
        response = self.client.get(reverse('homifi_app:property_api_list'))
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_property_api_detail_view_authenticated(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('homifi_app:property_api_detail', args=[self.property.pk]))
        self.assertEqual(response.status_code, 200)

    def test_property_api_detail_view_unauthenticated(self):
        response = self.client.get(reverse('homifi_app:property_api_detail', args=[self.property.pk]))
        self.assertEqual(response.status_code, 401)  # Unauthorized 