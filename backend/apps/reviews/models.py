"""
Review models for GlamConnect.
Allows clients to review completed bookings with ratings and comments.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class Review(models.Model):
    """
    Review model for completed bookings.

    Business rules:
    - One review per completed booking
    - Only clients can create reviews
    - Rating must be 1-5 stars
    - Artists can respond to reviews
    - Admin can flag/hide reviews for moderation
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review',
        db_index=True,
        help_text="The completed booking being reviewed"
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_written',
        db_index=True,
        limit_choices_to={'role': 'client'}
    )
    artist = models.ForeignKey(
        'profiles.MakeupArtistProfile',
        on_delete=models.CASCADE,
        related_name='reviews_received',
        db_index=True
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True,
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        help_text="Review comment from client"
    )
    is_visible = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Controls if review is publicly visible"
    )
    flagged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flagged for moderation (spam/inappropriate content)"
    )
    flagged_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for flagging"
    )
    artist_response = models.TextField(
        blank=True,
        null=True,
        help_text="Artist's response to the review"
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When artist responded"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews_review'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['artist', 'is_visible', '-created_at']),
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['rating', '-created_at']),
            models.Index(fields=['flagged', 'is_visible']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=1, rating__lte=5),
                name='valid_rating_range'
            ),
        ]

    def __str__(self):
        return f"Review by {self.client.full_name} for {self.artist.user.full_name} ({self.rating}⭐)"

    def clean(self):
        """Validate review data."""
        super().clean()

        # Ensure booking exists
        if not self.booking_id:
            raise ValidationError({
                'booking': 'A booking must be specified for the review.'
            })

        # Import here to avoid circular imports
        from apps.bookings.models import BookingStatus

        # Validate booking is completed
        if self.booking.status != BookingStatus.COMPLETED:
            raise ValidationError({
                'booking': 'Only completed bookings can be reviewed.'
            })

        # Validate client is the booking client
        if self.booking.client != self.client:
            raise ValidationError({
                'client': 'Only the client who made the booking can review it.'
            })

        # Validate artist matches booking artist
        if self.booking.artist != self.artist:
            raise ValidationError({
                'artist': 'Artist must match the booking artist.'
            })

        # Check for duplicate review
        if not self.pk:  # Only on creation
            if Review.objects.filter(booking=self.booking).exists():
                raise ValidationError({
                    'booking': 'This booking has already been reviewed.'
                })

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def add_artist_response(self, response_text):
        """
        Add or update artist response to the review.

        Args:
            response_text (str): The artist's response text

        Raises:
            ValidationError: If response is empty
        """
        if not response_text or not response_text.strip():
            raise ValidationError('Response text cannot be empty.')

        self.artist_response = response_text.strip()
        self.responded_at = timezone.now()
        self.save(update_fields=['artist_response', 'responded_at', 'updated_at'])

    def flag_for_moderation(self, reason=None):
        """
        Flag review for moderation (admin action).

        Args:
            reason (str, optional): Reason for flagging
        """
        self.flagged = True
        if reason:
            self.flagged_reason = reason
        self.save(update_fields=['flagged', 'flagged_reason', 'updated_at'])

    def unflag(self):
        """Remove flag from review (admin action)."""
        self.flagged = False
        self.flagged_reason = None
        self.save(update_fields=['flagged', 'flagged_reason', 'updated_at'])

    def hide(self):
        """Hide review from public view (admin action)."""
        self.is_visible = False
        self.save(update_fields=['is_visible', 'updated_at'])

    def show(self):
        """Make review visible to public (admin action)."""
        self.is_visible = True
        self.save(update_fields=['is_visible', 'updated_at'])

    @property
    def has_response(self):
        """Check if artist has responded."""
        return bool(self.artist_response)

    @property
    def is_recent(self):
        """Check if review was created in the last 30 days."""
        from datetime import timedelta
        return self.created_at >= timezone.now() - timedelta(days=30)
