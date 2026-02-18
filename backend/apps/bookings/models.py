"""
Booking models for GlamConnect.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class BookingStatus(models.TextChoices):
    """Booking status choices."""
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Service(models.Model):
    """Services offered by makeup artists."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(
        'profiles.MakeupArtistProfile',
        on_delete=models.CASCADE,
        related_name='services'
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration of the service in minutes"
    )
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services_service'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['artist', 'is_active']),
        ]

    def __str__(self):
        return f"{self.artist.user.full_name} - {self.name}"


class Booking(models.Model):
    """Booking model for client-artist appointments."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings_as_client',
        limit_choices_to={'role': 'client'}
    )
    artist = models.ForeignKey(
        'profiles.MakeupArtistProfile',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    booking_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True
    )
    location = models.CharField(max_length=255)
    client_notes = models.TextField(blank=True, null=True)
    artist_notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.CharField(
        max_length=10,
        choices=[('client', 'Client'), ('artist', 'Artist')],
        blank=True,
        null=True
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bookings_booking'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status', '-created_at']),
            models.Index(fields=['artist', 'status', 'booking_date']),
            models.Index(fields=['booking_date', 'status']),
            models.Index(fields=['booking_number']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(booking_date__gte=timezone.now().date()),
                name='booking_date_not_in_past'
            ),
        ]

    def __str__(self):
        return f"{self.booking_number} - {self.client.full_name} with {self.artist.user.full_name}"

    def save(self, *args, **kwargs):
        """Generate booking number if not exists."""
        if not self.booking_number:
            self.booking_number = self._generate_booking_number()

        # Set total_price from service if not set
        if not self.total_price and self.service:
            self.total_price = self.service.price

        super().save(*args, **kwargs)

    def clean(self):
        """Validate booking data."""
        super().clean()

        # Validate end_time > start_time
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({
                'end_time': 'End time must be after start time.'
            })

        # Validate booking date is not in the past
        if self.booking_date and self.booking_date < timezone.now().date():
            raise ValidationError({
                'booking_date': 'Booking date cannot be in the past.'
            })

        # Validate service belongs to the artist
        if self.service and self.artist and self.service.artist != self.artist:
            raise ValidationError({
                'service': 'This service does not belong to the selected artist.'
            })

    def _generate_booking_number(self):
        """Generate unique booking number."""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:6].upper()
        return f"BK{timestamp}{random_suffix}"

    def accept(self):
        """Accept the booking (artist only)."""
        if self.status != BookingStatus.PENDING:
            raise ValidationError('Only pending bookings can be accepted.')

        self.status = BookingStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at', 'updated_at'])

    def reject(self, reason=None):
        """Reject the booking (artist only)."""
        if self.status != BookingStatus.PENDING:
            raise ValidationError('Only pending bookings can be rejected.')

        self.status = BookingStatus.REJECTED
        if reason:
            self.artist_notes = reason
        self.save(update_fields=['status', 'artist_notes', 'updated_at'])

    def complete(self):
        """Mark booking as completed (artist only)."""
        if self.status != BookingStatus.ACCEPTED:
            raise ValidationError('Only accepted bookings can be marked as completed.')

        self.status = BookingStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Update artist's total bookings
        self.artist.total_bookings += 1
        self.artist.save(update_fields=['total_bookings', 'updated_at'])

    def cancel(self, cancelled_by, reason=None):
        """Cancel the booking."""
        if self.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise ValidationError('Cannot cancel completed or already cancelled bookings.')

        self.status = BookingStatus.CANCELLED
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_by', 'cancellation_reason', 'cancelled_at', 'updated_at'])

    @property
    def can_be_reviewed(self):
        """Check if booking can be reviewed."""
        return self.status == BookingStatus.COMPLETED and not hasattr(self, 'review')

    @property
    def is_upcoming(self):
        """Check if booking is upcoming."""
        return (
            self.status == BookingStatus.ACCEPTED and
            self.booking_date >= timezone.now().date()
        )

    @property
    def is_past(self):
        """Check if booking date has passed."""
        return self.booking_date < timezone.now().date()
