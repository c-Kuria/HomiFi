from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Property, PropertyImage, Inquiry, Favorite, SavedSearch

User = get_user_model()

class PropertyModelTest(TestCase):
    def setUp(self):
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

    def test_property_creation(self):
        self.assertEqual(self.property.title, 'Test Property')
        self.assertEqual(self.property.price, 100000)
        self.assertEqual(self.property.owner, self.user)

    def test_property_str(self):
        self.assertEqual(str(self.property), 'Test Property')

class PropertyImageModelTest(TestCase):
    def setUp(self):
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

    def test_property_image_str(self):
        image = PropertyImage.objects.create(
            property=self.property,
            image='test.jpg',
            is_primary=True
        )
        self.assertEqual(str(image), f'Image for {self.property.title}')

class InquiryModelTest(TestCase):
    def setUp(self):
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

    def test_inquiry_creation(self):
        inquiry = Inquiry.objects.create(
            property=self.property,
            user=self.user,
            name='Test User',
            email='test@example.com',
            message='Test message'
        )
        self.assertEqual(inquiry.property, self.property)
        self.assertEqual(inquiry.user, self.user)
        self.assertFalse(inquiry.is_read)

class FavoriteModelTest(TestCase):
    def setUp(self):
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

    def test_favorite_creation(self):
        favorite = Favorite.objects.create(
            user=self.user,
            property=self.property
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.property, self.property)

class SavedSearchModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='landlord'
        )

    def test_saved_search_creation(self):
        saved_search = SavedSearch.objects.create(
            user=self.user,
            query='test query',
            filters={'min_price': 100000, 'max_price': 200000},
            location='Test City'
        )
        self.assertEqual(saved_search.user, self.user)
        self.assertEqual(saved_search.query, 'test query')
        self.assertFalse(saved_search.notification_enabled) 