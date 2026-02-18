"""
Tests for reviews app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from apps.bookings.models import Booking, BookingStatus, Service
from apps.profiles.models import MakeupArtistProfile
from .models import Review

User = get_user_model()


class ReviewModelTest(TestCase):
    """Test cases for Review model."""

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
            bio='Test artist bio',
            hourly_rate=Decimal('100.00'),
            location='Test City'
        )

        # Create service
        self.service = Service.objects.create(
            artist=self.artist_profile,
            name='Test Service',
            description='Test description',
            price=Decimal('100.00'),
            duration_minutes=60
        )

        # Create completed booking
        self.booking = Booking.objects.create(
            client=self.client_user,
            artist=self.artist_profile,
            service=self.service,
            booking_date=timezone.now().date(),
            start_time='10:00',
            end_time='11:00',
            status=BookingStatus.COMPLETED,
            location='Test Location',
            total_price=Decimal('100.00')
        )
        self.booking.completed_at = timezone.now()
        self.booking.save()

    def test_create_valid_review(self):
        """Test creating a valid review."""
        review = Review.objects.create(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=5,
            comment='Excellent service!'
        )

        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent service!')
        self.assertTrue(review.is_visible)
        self.assertFalse(review.flagged)

    def test_one_review_per_booking(self):
        """Test that only one review can be created per booking."""
        Review.objects.create(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=5,
            comment='First review'
        )

        # Try to create second review for same booking
        with self.assertRaises(ValidationError):
            Review.objects.create(
                booking=self.booking,
                client=self.client_user,
                artist=self.artist_profile,
                rating=4,
                comment='Second review'
            )

    def test_rating_validation(self):
        """Test that rating must be between 1 and 5."""
        # Test rating below minimum
        with self.assertRaises(ValidationError):
            Review.objects.create(
                booking=self.booking,
                client=self.client_user,
                artist=self.artist_profile,
                rating=0,
                comment='Invalid rating'
            )

        # Test rating above maximum
        with self.assertRaises(ValidationError):
            Review.objects.create(
                booking=self.booking,
                client=self.client_user,
                artist=self.artist_profile,
                rating=6,
                comment='Invalid rating'
            )

    def test_artist_response(self):
        """Test artist responding to review."""
        review = Review.objects.create(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=5,
            comment='Great service!'
        )

        # Add artist response
        review.add_artist_response('Thank you for your feedback!')

        self.assertEqual(review.artist_response, 'Thank you for your feedback!')
        self.assertIsNotNone(review.responded_at)
        self.assertTrue(review.has_response)

    def test_flag_review(self):
        """Test flagging a review for moderation."""
        review = Review.objects.create(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=1,
            comment='Spam content'
        )

        review.flag_for_moderation(reason='Contains spam')

        self.assertTrue(review.flagged)
        self.assertEqual(review.flagged_reason, 'Contains spam')

    def test_hide_review(self):
        """Test hiding a review from public view."""
        review = Review.objects.create(
            booking=self.booking,
            client=self.client_user,
            artist=self.artist_profile,
            rating=5,
            comment='Test review'
        )

        review.hide()

        self.assertFalse(review.is_visible)


class ReviewPermissionTest(TestCase):
    """Test cases for review permissions."""

    # Add permission tests here
    pass
