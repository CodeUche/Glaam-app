"""
Tests for bookings app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Booking, Service, BookingStatus
from apps.profiles.models import MakeupArtistProfile, Availability
from .utils import check_artist_availability

User = get_user_model()


class BookingModelTest(TestCase):
    """Test cases for Booking model."""

    def setUp(self):
        """Set up test data."""
        # Create client user
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Client',
            role='client'
        )

        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test bio',
            hourly_rate=100.00,
            location='Test City'
        )

        # Create service
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Bridal Makeup',
            description='Beautiful bridal makeup',
            price=150.00,
            duration_minutes=120,
            category='bridal'
        )

        # Create availability
        Availability.objects.create(
            artist=self.artist_profile,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

    def test_booking_creation(self):
        """Test creating a booking."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test Location'
        )

        self.assertIsNotNone(booking.booking_number)
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.total_price, self.service.price)

    def test_booking_accept(self):
        """Test accepting a booking."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test Location'
        )

        booking.accept()
        self.assertEqual(booking.status, BookingStatus.ACCEPTED)
        self.assertIsNotNone(booking.accepted_at)

    def test_booking_complete(self):
        """Test completing a booking."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test Location'
        )

        booking.accept()
        booking.complete()

        self.assertEqual(booking.status, BookingStatus.COMPLETED)
        self.assertIsNotNone(booking.completed_at)


class BookingAPITest(APITestCase):
    """Test cases for Booking API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create client user
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Client',
            role='client'
        )

        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test bio',
            hourly_rate=100.00,
            location='Test City'
        )

        # Create service
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Bridal Makeup',
            description='Beautiful bridal makeup',
            price=150.00,
            duration_minutes=120,
            category='bridal'
        )

        # Create availability
        Availability.objects.create(
            artist=self.artist_profile,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        self.client_api = APIClient()

    def test_create_booking_as_client(self):
        """Test creating a booking as a client."""
        self.client_api.force_authenticate(user=self.client_user)

        tomorrow = timezone.now().date() + timedelta(days=1)
        # Ensure tomorrow is a Monday (day_of_week=0)
        while tomorrow.weekday() != 0:
            tomorrow += timedelta(days=1)

        data = {
            'artist': str(self.artist_profile.id),
            'service': str(self.service.id),
            'booking_date': tomorrow.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Test Location',
            'client_notes': 'Please bring extra makeup'
        }

        response = self.client_api.post('/api/v1/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_number', response.data)

    def test_list_bookings_as_client(self):
        """Test listing bookings as a client."""
        self.client_api.force_authenticate(user=self.client_user)

        # Create a booking
        tomorrow = timezone.now().date() + timedelta(days=1)
        Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test Location'
        )

        response = self.client_api.get('/api/v1/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class AvailabilityUtilTest(TestCase):
    """Test cases for availability checking utilities."""

    def setUp(self):
        """Set up test data."""
        # Create artist user
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Artist',
            role='artist'
        )

        # Create artist profile
        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test bio',
            hourly_rate=100.00,
            location='Test City'
        )

        # Create service
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Bridal Makeup',
            description='Beautiful bridal makeup',
            price=150.00,
            duration_minutes=120,
            category='bridal'
        )

        # Create availability for Monday
        Availability.objects.create(
            artist=self.artist_profile,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

    def test_check_availability_success(self):
        """Test availability check for valid time slot."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        # Ensure tomorrow is a Monday
        while tomorrow.weekday() != 0:
            tomorrow += timedelta(days=1)

        is_available = check_artist_availability(
            artist=self.artist_profile,
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )

        self.assertTrue(is_available)

    def test_check_availability_with_conflict(self):
        """Test availability check with conflicting booking."""
        # Create client user
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Client',
            role='client'
        )

        tomorrow = timezone.now().date() + timedelta(days=1)
        # Ensure tomorrow is a Monday
        while tomorrow.weekday() != 0:
            tomorrow += timedelta(days=1)

        # Create existing booking
        Booking.objects.create(
            client=client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test Location',
            status=BookingStatus.ACCEPTED
        )

        # Try to check availability for overlapping time
        is_available = check_artist_availability(
            artist=self.artist_profile,
            booking_date=tomorrow,
            start_time=time(11, 0),
            end_time=time(13, 0)
        )

        self.assertFalse(is_available)
