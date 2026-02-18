"""
Tests for services app.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.profiles.models import MakeupArtistProfile
from .models import Service, ServiceCategory

User = get_user_model()


class ServiceModelTests(TestCase):
    """Tests for Service model."""

    def setUp(self):
        """Set up test data."""
        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Artist',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test artist',
            hourly_rate=Decimal('100.00'),
            location='Test City'
        )

    def test_create_service(self):
        """Test creating a service."""
        service = Service.objects.create(
            artist=self.artist_profile,
            name='Bridal Makeup',
            description='Complete bridal makeup package',
            category=ServiceCategory.BRIDAL,
            price=Decimal('250.00'),
            duration=120
        )

        self.assertEqual(service.name, 'Bridal Makeup')
        self.assertEqual(service.category, ServiceCategory.BRIDAL)
        self.assertEqual(service.price, Decimal('250.00'))
        self.assertEqual(service.duration, 120)
        self.assertTrue(service.is_active)
        self.assertEqual(service.booking_count, 0)

    def test_service_str_representation(self):
        """Test service string representation."""
        service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            category=ServiceCategory.NATURAL,
            price=Decimal('100.00'),
            duration=60
        )

        expected = f"{self.artist_profile.user.full_name} - Test Service"
        self.assertEqual(str(service), expected)

    def test_duration_hours_property(self):
        """Test duration_hours property calculation."""
        service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            category=ServiceCategory.NATURAL,
            price=Decimal('100.00'),
            duration=90
        )

        self.assertEqual(service.duration_hours, 1.5)

    def test_is_available_property(self):
        """Test is_available property."""
        service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            category=ServiceCategory.NATURAL,
            price=Decimal('100.00'),
            duration=60
        )

        # Service is active and artist is available
        self.assertTrue(service.is_available)

        # Deactivate service
        service.is_active = False
        service.save()
        self.assertFalse(service.is_available)

    def test_increment_booking_count(self):
        """Test increment_booking_count method."""
        service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            category=ServiceCategory.NATURAL,
            price=Decimal('100.00'),
            duration=60
        )

        initial_count = service.booking_count
        service.increment_booking_count()

        self.assertEqual(service.booking_count, initial_count + 1)


class ServiceAPITests(APITestCase):
    """Tests for Service API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Artist',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test artist',
            hourly_rate=Decimal('100.00'),
            location='Test City'
        )

        # Create client user
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='John',
            last_name='Client',
            role='client'
        )

        # Create test service
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            category=ServiceCategory.NATURAL,
            price=Decimal('100.00'),
            duration=60
        )

    def test_list_services(self):
        """Test listing services."""
        url = '/api/services/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_service(self):
        """Test retrieving a service."""
        url = f'/api/services/{self.service.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Service')

    def test_create_service_as_artist(self):
        """Test creating a service as an artist."""
        self.client.force_authenticate(user=self.artist_user)

        url = '/api/services/'
        data = {
            'name': 'New Service',
            'description': 'New service description',
            'category': ServiceCategory.BRIDAL,
            'price': '200.00',
            'duration': 90
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 2)

    def test_create_service_as_client_fails(self):
        """Test that clients cannot create services."""
        self.client.force_authenticate(user=self.client_user)

        url = '/api/services/'
        data = {
            'name': 'New Service',
            'description': 'New service description',
            'category': ServiceCategory.BRIDAL,
            'price': '200.00',
            'duration': 90
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_service(self):
        """Test artist updating their own service."""
        self.client.force_authenticate(user=self.artist_user)

        url = f'/api/services/{self.service.id}/'
        data = {
            'name': 'Updated Service',
            'description': 'Updated description',
            'category': ServiceCategory.GLAM,
            'price': '150.00',
            'duration': 75
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.service.refresh_from_db()
        self.assertEqual(self.service.name, 'Updated Service')

    def test_delete_own_service(self):
        """Test artist deleting their own service."""
        self.client.force_authenticate(user=self.artist_user)

        url = f'/api/services/{self.service.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Service.objects.count(), 0)

    def test_get_my_services(self):
        """Test getting artist's own services."""
        self.client.force_authenticate(user=self.artist_user)

        url = '/api/services/my_services/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_toggle_service_active(self):
        """Test toggling service active status."""
        self.client.force_authenticate(user=self.artist_user)

        url = f'/api/services/{self.service.id}/toggle_active/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)

    def test_get_categories(self):
        """Test getting service categories."""
        url = '/api/services/categories/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
