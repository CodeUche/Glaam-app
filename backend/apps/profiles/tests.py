"""
Tests for the profiles app.

Run tests with:
    python manage.py test apps.profiles
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal

from .models import (
    ClientProfile,
    MakeupArtistProfile,
    PortfolioImage,
    Favorite,
    Availability,
    AvailabilityException
)

User = get_user_model()


class ClientProfileModelTest(TestCase):
    """Test cases for ClientProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Client',
            role='client'
        )

    def test_create_client_profile(self):
        """Test creating a client profile."""
        profile = ClientProfile.objects.create(
            user=self.user,
            bio='Test bio',
            preferred_location='New York'
        )
        self.assertEqual(str(profile), 'Client: Test Client')
        self.assertEqual(profile.user, self.user)

    def test_notification_preferences_default(self):
        """Test notification preferences default to empty dict."""
        profile = ClientProfile.objects.create(user=self.user)
        self.assertEqual(profile.notification_preferences, {})


class MakeupArtistProfileModelTest(TestCase):
    """Test cases for MakeupArtistProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )

    def test_create_artist_profile(self):
        """Test creating an artist profile."""
        profile = MakeupArtistProfile.objects.create(
            user=self.user,
            bio='Professional makeup artist',
            specialties=['bridal', 'glam'],
            years_of_experience=5,
            hourly_rate=Decimal('75.00'),
            location='Los Angeles'
        )
        self.assertEqual(str(profile), 'Artist: Test Artist')
        self.assertEqual(profile.specialties, ['bridal', 'glam'])
        self.assertEqual(profile.average_rating, Decimal('0.00'))
        self.assertTrue(profile.is_available)
        self.assertFalse(profile.verified)

    def test_artist_profile_defaults(self):
        """Test default values for artist profile."""
        profile = MakeupArtistProfile.objects.create(
            user=self.user,
            bio='Test',
            hourly_rate=Decimal('50.00'),
            location='Test City'
        )
        self.assertEqual(profile.years_of_experience, 0)
        self.assertEqual(profile.total_reviews, 0)
        self.assertEqual(profile.total_bookings, 0)
        self.assertTrue(profile.is_available)


class PortfolioImageModelTest(TestCase):
    """Test cases for PortfolioImage model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )
        self.artist = MakeupArtistProfile.objects.create(
            user=self.user,
            bio='Test',
            hourly_rate=Decimal('50.00'),
            location='Test City'
        )

    def test_portfolio_image_ordering(self):
        """Test portfolio images are ordered by display_order."""
        img1 = PortfolioImage.objects.create(
            artist=self.artist,
            image_url='image1.jpg',
            display_order=2
        )
        img2 = PortfolioImage.objects.create(
            artist=self.artist,
            image_url='image2.jpg',
            display_order=1
        )

        images = self.artist.portfolio_images.all()
        self.assertEqual(images[0], img2)  # Lower display_order comes first
        self.assertEqual(images[1], img1)


class FavoriteModelTest(TestCase):
    """Test cases for Favorite model."""

    def setUp(self):
        """Set up test data."""
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Client',
            role='client'
        )
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )
        self.artist = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test',
            hourly_rate=Decimal('50.00'),
            location='Test City'
        )

    def test_create_favorite(self):
        """Test creating a favorite."""
        favorite = Favorite.objects.create(
            client=self.client_user,
            artist=self.artist
        )
        self.assertEqual(favorite.client, self.client_user)
        self.assertEqual(favorite.artist, self.artist)

    def test_unique_favorite(self):
        """Test that a client can't favorite the same artist twice."""
        Favorite.objects.create(
            client=self.client_user,
            artist=self.artist
        )
        # This should raise an integrity error
        with self.assertRaises(Exception):
            Favorite.objects.create(
                client=self.client_user,
                artist=self.artist
            )


class AvailabilityModelTest(TestCase):
    """Test cases for Availability model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )
        self.artist = MakeupArtistProfile.objects.create(
            user=self.user,
            bio='Test',
            hourly_rate=Decimal('50.00'),
            location='Test City'
        )

    def test_create_availability(self):
        """Test creating availability."""
        from datetime import time
        avail = Availability.objects.create(
            artist=self.artist,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        self.assertEqual(avail.day_of_week, 0)
        self.assertTrue(avail.is_active)


# API Tests
class ArtistProfileAPITest(APITestCase):
    """Test cases for Artist Profile API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Professional makeup artist',
            specialties=['bridal', 'glam'],
            years_of_experience=5,
            hourly_rate=Decimal('75.00'),
            location='Los Angeles',
            is_available=True
        )

        # Create client user
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='John',
            last_name='Smith',
            role='client'
        )

    def test_list_artists_unauthenticated(self):
        """Test that unauthenticated users can view artist list."""
        response = self.client_api.get('/api/profiles/artists/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_artist_detail(self):
        """Test retrieving artist detail."""
        response = self.client_api.get(f'/api/profiles/artists/{self.artist_profile.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'artist@test.com')

    def test_filter_artists_by_location(self):
        """Test filtering artists by location."""
        response = self.client_api.get('/api/profiles/artists/?location=Los%20Angeles')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_artist_profile_requires_authentication(self):
        """Test that creating artist profile requires authentication."""
        data = {
            'bio': 'New artist',
            'hourly_rate': '50.00',
            'location': 'New York'
        }
        response = self.client_api.post('/api/profiles/artists/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_artist_profile_requires_artist_role(self):
        """Test that creating artist profile requires artist role."""
        self.client_api.force_authenticate(user=self.client_user)
        data = {
            'bio': 'New artist',
            'hourly_rate': '50.00',
            'location': 'New York'
        }
        response = self.client_api.post('/api/profiles/artists/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FavoriteAPITest(APITestCase):
    """Test cases for Favorite API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create users
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='John',
            last_name='Smith',
            role='client'
        )
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Professional makeup artist',
            hourly_rate=Decimal('75.00'),
            location='Los Angeles'
        )

    def test_create_favorite_requires_authentication(self):
        """Test that creating favorite requires authentication."""
        data = {'artist': str(self.artist_profile.id)}
        response = self.client_api.post('/api/profiles/favorites/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_favorite(self):
        """Test creating a favorite."""
        self.client_api.force_authenticate(user=self.client_user)
        data = {'artist': str(self.artist_profile.id)}
        response = self.client_api.post('/api/profiles/favorites/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_favorites(self):
        """Test listing user's favorites."""
        self.client_api.force_authenticate(user=self.client_user)
        Favorite.objects.create(client=self.client_user, artist=self.artist_profile)

        response = self.client_api.get('/api/profiles/favorites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PortfolioImageAPITest(APITestCase):
    """Test cases for Portfolio Image API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Professional makeup artist',
            hourly_rate=Decimal('75.00'),
            location='Los Angeles'
        )

    def test_list_portfolio_images_unauthenticated(self):
        """Test that unauthenticated users can view portfolio."""
        response = self.client_api.get('/api/profiles/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_portfolio_image_requires_authentication(self):
        """Test that creating portfolio image requires authentication."""
        data = {
            'category': 'bridal',
            'caption': 'Test image'
        }
        response = self.client_api.post('/api/profiles/portfolio/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# Additional test classes can be added for:
# - AvailabilityAPITest
# - AvailabilityExceptionAPITest
# - SerializerTests
# - FilterTests
