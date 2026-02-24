"""
Tests for bookings app.

Covers: Booking model lifecycle, validation, API endpoints,
availability checking, and permission enforcement.
"""

import pytest

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta
from unittest.mock import patch

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Booking, BookingStatus
from apps.services.models import Service
from apps.profiles.models import MakeupArtistProfile, Availability
from .utils import check_artist_availability

User = get_user_model()


class BookingModelTest(TestCase):
    """Test cases for Booking model lifecycle and business logic."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Client',
            role='client',
        )
        self.artist_user = User.objects.create_user(
            email='artist@test.com',
            password='testpass123',
            first_name='Maria',
            last_name='Artist',
            role='artist',
        )
        self.artist_profile, _ = MakeupArtistProfile.objects.get_or_create(
            user=self.artist_user,
            defaults={
                'bio': 'Test bio',
                'hourly_rate': 100.00,
                'location': 'Test City',
            }
        )
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Bridal Makeup',
            description='Beautiful bridal makeup',
            price=150.00,
            duration=120,
            category='bridal',
        )
        Availability.objects.get_or_create(
            artist=self.artist_profile,
            day_of_week=0,
            defaults={'start_time': time(9, 0), 'end_time': time(17, 0)},
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def _make_booking(self, **kwargs):
        defaults = dict(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test Location',
        )
        defaults.update(kwargs)
        return Booking.objects.create(**defaults)

    # ── Model basics ──────────────────────────────────────────────────────────

    def test_booking_number_auto_generated(self):
        booking = self._make_booking()
        self.assertIsNotNone(booking.booking_number)
        self.assertTrue(booking.booking_number.startswith('BK'))

    def test_total_price_auto_set_from_service(self):
        booking = self._make_booking()
        self.assertEqual(booking.total_price, self.service.price)

    def test_default_status_is_pending(self):
        booking = self._make_booking()
        self.assertEqual(booking.status, BookingStatus.PENDING)

    def test_str_representation(self):
        booking = self._make_booking()
        self.assertIn(booking.booking_number, str(booking))

    # ── Status transitions ────────────────────────────────────────────────────

    def test_accept_pending_booking(self):
        booking = self._make_booking()
        booking.accept()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.ACCEPTED)
        self.assertIsNotNone(booking.accepted_at)

    def test_cannot_accept_non_pending_booking(self):
        booking = self._make_booking()
        booking.accept()
        with self.assertRaises(ValidationError):
            booking.accept()  # Already accepted

    def test_reject_pending_booking(self):
        booking = self._make_booking()
        booking.reject(reason='Not available')
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.REJECTED)
        self.assertEqual(booking.artist_notes, 'Not available')

    def test_complete_accepted_booking(self):
        booking = self._make_booking()
        booking.accept()
        booking.complete()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.COMPLETED)
        self.assertIsNotNone(booking.completed_at)

    def test_cannot_complete_pending_booking(self):
        booking = self._make_booking()
        with self.assertRaises(ValidationError):
            booking.complete()

    def test_cancel_by_client(self):
        booking = self._make_booking()
        booking.cancel(cancelled_by='client', reason='Change of plans')
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED)
        self.assertEqual(booking.cancelled_by, 'client')
        self.assertEqual(booking.cancellation_reason, 'Change of plans')
        self.assertIsNotNone(booking.cancelled_at)

    def test_cancel_by_artist(self):
        booking = self._make_booking()
        booking.cancel(cancelled_by='artist', reason='Emergency')
        self.assertEqual(booking.cancelled_by, 'artist')

    def test_cancel_by_system(self):
        booking = self._make_booking()
        booking.cancel(cancelled_by='system', reason='Booking expired')
        self.assertEqual(booking.cancelled_by, 'system')

    def test_cannot_cancel_completed_booking(self):
        booking = self._make_booking()
        booking.accept()
        booking.complete()
        with self.assertRaises(ValidationError):
            booking.cancel(cancelled_by='client')

    # ── Validation ────────────────────────────────────────────────────────────

    def test_clean_end_time_before_start_time_raises(self):
        booking = Booking(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.tomorrow,
            start_time=time(12, 0),
            end_time=time(10, 0),  # Before start_time
            location='Test',
            total_price=150.00,
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn('end_time', ctx.exception.message_dict)

    def test_clean_past_booking_date_raises(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        booking = Booking(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=yesterday,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test',
            total_price=150.00,
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn('booking_date', ctx.exception.message_dict)

    # ── Properties ───────────────────────────────────────────────────────────

    def test_is_upcoming_property(self):
        booking = self._make_booking()
        booking.accept()
        self.assertTrue(booking.is_upcoming)

    def test_can_be_reviewed_after_complete(self):
        booking = self._make_booking()
        booking.accept()
        booking.complete()
        booking.refresh_from_db()
        self.assertTrue(booking.can_be_reviewed)


class AvailabilityUtilTest(TestCase):
    """Test cases for availability checking utilities."""

    def setUp(self):
        self.artist_user = User.objects.create_user(
            email='avail_artist@test.com',
            password='testpass123',
            role='artist',
        )
        self.artist_profile, _ = MakeupArtistProfile.objects.get_or_create(
            user=self.artist_user,
            defaults={'bio': 'Test', 'hourly_rate': 80.00, 'location': 'NYC'},
        )
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Glam Makeup',
            description='Full glam',
            price=100.00,
            duration=60,
            category='glam',
        )
        self.client_user = User.objects.create_user(
            email='avail_client@test.com',
            password='testpass123',
            role='client',
        )
        # Create Monday availability
        Availability.objects.get_or_create(
            artist=self.artist_profile,
            day_of_week=0,
            defaults={'start_time': time(9, 0), 'end_time': time(17, 0)},
        )
        # Find next Monday
        today = timezone.now().date()
        days_ahead = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_ahead)

    def test_check_availability_within_hours(self):
        available = check_artist_availability(
            artist=self.artist_profile,
            booking_date=self.next_monday,
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        self.assertTrue(available)

    def test_check_availability_outside_hours(self):
        available = check_artist_availability(
            artist=self.artist_profile,
            booking_date=self.next_monday,
            start_time=time(18, 0),
            end_time=time(20, 0),
        )
        self.assertFalse(available)

    def test_check_availability_conflict_with_existing_booking(self):
        Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.next_monday,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='NYC',
            status=BookingStatus.ACCEPTED,
        )
        available = check_artist_availability(
            artist=self.artist_profile,
            booking_date=self.next_monday,
            start_time=time(11, 0),
            end_time=time(13, 0),
        )
        self.assertFalse(available)

    def test_check_availability_adjacent_booking_is_ok(self):
        """Booking starting exactly when another ends should be available."""
        Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.next_monday,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='NYC',
            status=BookingStatus.ACCEPTED,
        )
        available = check_artist_availability(
            artist=self.artist_profile,
            booking_date=self.next_monday,
            start_time=time(12, 0),
            end_time=time(14, 0),
        )
        self.assertTrue(available)


class BookingAPITest(APITestCase):
    """Test cases for Booking API endpoints."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            email='api_client@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Client',
            role='client',
        )
        self.artist_user = User.objects.create_user(
            email='api_artist@test.com',
            password='testpass123',
            first_name='Maria',
            last_name='Artist',
            role='artist',
        )
        self.artist_profile, _ = MakeupArtistProfile.objects.get_or_create(
            user=self.artist_user,
            defaults={
                'bio': 'Professional artist',
                'hourly_rate': 100.00,
                'location': 'NYC',
                'is_available': True,
            },
        )
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Bridal Makeup',
            description='Full bridal package',
            price=250.00,
            duration=120,
            category='bridal',
            is_active=True,
        )
        # Create Monday availability
        Availability.objects.get_or_create(
            artist=self.artist_profile,
            day_of_week=0,
            defaults={'start_time': time(9, 0), 'end_time': time(17, 0)},
        )
        today = timezone.now().date()
        days_ahead = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_ahead)

        self.client_api = APIClient()
        self.artist_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)
        self.artist_api.force_authenticate(user=self.artist_user)

    def _booking_data(self):
        return {
            'artist': str(self.artist_profile.id),
            'service': str(self.service.id),
            'booking_date': self.next_monday.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Test Location',
        }

    @patch('apps.bookings.views.send_booking_notification.delay')
    def test_client_can_create_booking(self, mock_task):
        response = self.client_api.post('/api/v1/bookings/', self._booking_data())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_number', response.data)
        mock_task.assert_called_once()

    def test_artist_cannot_create_booking(self):
        response = self.artist_api.post('/api/v1/bookings/', self._booking_data())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_booking(self):
        anon = APIClient()
        response = anon.post('/api/v1/bookings/', self._booking_data())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_can_list_own_bookings(self):
        Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.next_monday,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test',
        )
        response = self.client_api.get('/api/v1/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)

    @patch('apps.bookings.views.send_booking_notification.delay')
    def test_artist_can_accept_booking(self, mock_task):
        booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.next_monday,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test',
        )
        response = self.artist_api.post(f'/api/v1/bookings/{booking.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')

    @patch('apps.bookings.views.send_booking_notification.delay')
    def test_client_can_cancel_own_booking(self, mock_task):
        booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.next_monday,
            start_time=time(10, 0),
            end_time=time(12, 0),
            location='Test',
        )
        response = self.client_api.post(
            f'/api/v1/bookings/{booking.id}/cancel/',
            {'reason': 'Change of plans'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')

    def test_client_cannot_cancel_another_clients_booking(self):
        other_client = User.objects.create_user(
            email='other_client@test.com',
            password='testpass123',
            role='client',
        )
        booking = Booking.objects.create(
            client=other_client,
            artist=self.artist_profile,
            service=self.service,
            booking_date=self.next_monday,
            start_time=time(13, 0),
            end_time=time(15, 0),
            location='Test',
        )
        response = self.client_api.post(f'/api/v1/bookings/{booking.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_past_booking_date_rejected(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        data = self._booking_data()
        data['booking_date'] = yesterday.isoformat()
        response = self.client_api.post('/api/v1/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_end_time_before_start_time_rejected(self):
        data = self._booking_data()
        data['start_time'] = '14:00:00'
        data['end_time'] = '12:00:00'
        response = self.client_api.post('/api/v1/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
