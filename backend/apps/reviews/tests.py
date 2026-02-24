"""
Tests for reviews app.

Covers: Review model lifecycle, validation, API endpoints,
artist response, moderation, and rating updates.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from apps.bookings.models import Booking, BookingStatus
from apps.services.models import Service
from apps.profiles.models import MakeupArtistProfile
from .models import Review

User = get_user_model()


class ReviewModelTest(TestCase):
    """Test cases for Review model business logic."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            email='review_client@test.com',
            password='testpass123',
            first_name='Review',
            last_name='Client',
            role='client',
        )
        self.artist_user = User.objects.create_user(
            email='review_artist@test.com',
            password='testpass123',
            first_name='Review',
            last_name='Artist',
            role='artist',
        )
        self.artist_profile, _ = MakeupArtistProfile.objects.get_or_create(
            user=self.artist_user,
            defaults={
                'bio': 'Test artist bio',
                'hourly_rate': Decimal('100.00'),
                'location': 'Test City',
            }
        )
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            price=Decimal('100.00'),
            duration=60,
            category='natural',
        )
        # Create a completed booking (bypass clean() since status is set directly)
        self.booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=timezone.now().date(),
            start_time='10:00',
            end_time='11:00',
            status=BookingStatus.COMPLETED,
            location='Test Location',
            total_price=Decimal('100.00'),
        )
        self.booking.completed_at = timezone.now()
        self.booking.save(update_fields=['completed_at'])

    def _make_review(self, **kwargs):
        defaults = dict(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=5,
            comment='Great service! Very professional.',
        )
        defaults.update(kwargs)
        return Review.objects.create(**defaults)

    # ── Model basics ──────────────────────────────────────────────────────────

    def test_create_valid_review(self):
        review = self._make_review()
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_visible)
        self.assertFalse(review.flagged)

    def test_one_review_per_booking_enforced(self):
        """OneToOne constraint: second review for same booking must fail."""
        self._make_review()
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            Review.objects.create(
                booking=self.booking,
                client=self.client_user,
                artist=self.artist_profile,
                rating=3,
                comment='Second review attempt.',
            )

    def test_str_representation(self):
        review = self._make_review()
        self.assertIn(str(review.rating), str(review))

    # ── Rating validation ─────────────────────────────────────────────────────

    def test_rating_below_minimum_raises(self):
        with self.assertRaises(ValidationError):
            r = Review(
                booking=self.booking,
                client=self.client_user,
                artist=self.artist_profile,
                rating=0,
                comment='Bad rating value',
            )
            r.full_clean()

    def test_rating_above_maximum_raises(self):
        with self.assertRaises(ValidationError):
            r = Review(
                booking=self.booking,
                client=self.client_user,
                artist=self.artist_profile,
                rating=6,
                comment='Too high rating',
            )
            r.full_clean()

    # ── Artist response ───────────────────────────────────────────────────────

    def test_artist_can_add_response(self):
        review = self._make_review()
        review.add_artist_response('Thank you for your kind words!')
        review.refresh_from_db()
        self.assertEqual(review.artist_response, 'Thank you for your kind words!')
        self.assertIsNotNone(review.responded_at)
        self.assertTrue(review.has_response)

    def test_is_recent_property(self):
        review = self._make_review()
        self.assertTrue(review.is_recent)

    # ── Moderation ────────────────────────────────────────────────────────────

    def test_flag_review(self):
        review = self._make_review()
        review.flag_for_moderation(reason='Spam content detected')
        review.refresh_from_db()
        self.assertTrue(review.flagged)
        self.assertEqual(review.flagged_reason, 'Spam content detected')

    def test_unflag_review(self):
        review = self._make_review()
        review.flag_for_moderation(reason='Test')
        review.unflag()
        review.refresh_from_db()
        self.assertFalse(review.flagged)
        self.assertIsNone(review.flagged_reason)

    def test_hide_review(self):
        review = self._make_review()
        review.hide()
        review.refresh_from_db()
        self.assertFalse(review.is_visible)

    def test_show_review(self):
        review = self._make_review()
        review.hide()
        review.show()
        review.refresh_from_db()
        self.assertTrue(review.is_visible)


class ReviewAPITest(APITestCase):
    """Test cases for Review API endpoints."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            email='api_review_client@test.com',
            password='testpass123',
            first_name='API',
            last_name='Client',
            role='client',
        )
        self.artist_user = User.objects.create_user(
            email='api_review_artist@test.com',
            password='testpass123',
            first_name='API',
            last_name='Artist',
            role='artist',
        )
        self.artist_profile, _ = MakeupArtistProfile.objects.get_or_create(
            user=self.artist_user,
            defaults={
                'bio': 'Pro artist',
                'hourly_rate': Decimal('120.00'),
                'location': 'Brooklyn',
                'is_available': True,
            }
        )
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Evening Glam',
            description='Full glam look',
            price=Decimal('180.00'),
            duration=90,
            category='glam',
            is_active=True,
        )
        self.booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=timezone.now().date(),
            start_time='14:00',
            end_time='15:30',
            status=BookingStatus.COMPLETED,
            location='Brooklyn Studio',
            total_price=Decimal('180.00'),
        )
        self.booking.completed_at = timezone.now()
        self.booking.save(update_fields=['completed_at'])

        self.client_api = APIClient()
        self.artist_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)
        self.artist_api.force_authenticate(user=self.artist_user)

    @patch('apps.reviews.signals.update_artist_rating')
    def test_client_can_create_review(self, mock_task):
        data = {
            'booking': str(self.booking.id),
            'rating': 5,
            'comment': 'Absolutely amazing work! Very professional.',
        }
        response = self.client_api.post('/api/v1/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)

    def test_artist_cannot_create_review(self):
        data = {
            'booking': str(self.booking.id),
            'rating': 5,
            'comment': 'Self review attempt',
        }
        response = self.artist_api.post('/api/v1/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_review_non_completed_booking(self):
        pending_booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=timezone.now().date() + timedelta(days=1),
            start_time='10:00',
            end_time='11:30',
            status=BookingStatus.PENDING,
            location='Test',
            total_price=Decimal('180.00'),
        )
        data = {
            'booking': str(pending_booking.id),
            'rating': 4,
            'comment': 'Great job (but booking not done yet)',
        }
        response = self.client_api.post('/api/v1/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.reviews.signals.update_artist_rating')
    def test_artist_can_respond_to_review(self, mock_task):
        review = Review.objects.create(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=4,
            comment='Very good, would recommend.',
        )
        data = {'response': 'Thank you so much! It was a pleasure.'}
        response = self.artist_api.post(f'/api/v1/reviews/{review.id}/respond/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get('artist_response'))

    def test_list_reviews_is_public(self):
        anon = APIClient()
        response = anon.get('/api/v1/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.reviews.signals.update_artist_rating')
    def test_short_comment_rejected(self, mock_task):
        data = {
            'booking': str(self.booking.id),
            'rating': 3,
            'comment': 'Ok',  # Too short (< 10 chars)
        }
        response = self.client_api.post('/api/v1/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
