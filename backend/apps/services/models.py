"""
Service models for GlamConnect.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class ServiceCategory(models.TextChoices):
    """Service category choices."""
    BRIDAL = 'bridal', _('Bridal Makeup')
    EDITORIAL = 'editorial', _('Editorial Makeup')
    NATURAL = 'natural', _('Natural/Everyday Makeup')
    GLAM = 'glam', _('Glamour Makeup')
    SFX = 'sfx', _('Special Effects Makeup')
    AIRBRUSH = 'airbrush', _('Airbrush Makeup')
    THEATRICAL = 'theatrical', _('Theatrical Makeup')
    CONSULTATION = 'consultation', _('Consultation')
    OTHER = 'other', _('Other')


class Service(models.Model):
    """
    Service model representing makeup services offered by artists.

    Each service is linked to a specific makeup artist and includes:
    - Service details (name, description, category)
    - Pricing and duration information
    - Availability status
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(
        'profiles.MakeupArtistProfile',
        on_delete=models.CASCADE,
        related_name='services',
        db_index=True,
        help_text=_('The makeup artist offering this service')
    )
    name = models.CharField(
        _('service name'),
        max_length=200,
        help_text=_('Name of the service (e.g., "Bridal Makeup Package")')
    )
    description = models.TextField(
        _('description'),
        help_text=_('Detailed description of what the service includes')
    )
    category = models.CharField(
        _('category'),
        max_length=20,
        choices=ServiceCategory.choices,
        default=ServiceCategory.OTHER,
        db_index=True,
        help_text=_('Category of the makeup service')
    )
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Service price in local currency')
    )
    duration = models.PositiveIntegerField(
        _('duration'),
        validators=[MinValueValidator(15), MaxValueValidator(480)],
        help_text=_('Service duration in minutes (15 min to 8 hours)')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        db_index=True,
        help_text=_('Whether this service is currently available for booking')
    )
    booking_count = models.PositiveIntegerField(
        _('booking count'),
        default=0,
        help_text=_('Total number of times this service has been booked')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'services_service'
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['artist', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['artist', 'category']),
            models.Index(fields=['-booking_count']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='service_price_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(duration__gte=15) & models.Q(duration__lte=480),
                name='service_duration_valid_range'
            ),
        ]

    def __str__(self):
        return f"{self.artist.user.full_name} - {self.name}"

    def increment_booking_count(self):
        """Increment the booking count for this service."""
        self.booking_count = models.F('booking_count') + 1
        self.save(update_fields=['booking_count', 'updated_at'])
        self.refresh_from_db()

    @property
    def duration_hours(self):
        """Return duration in hours as a decimal."""
        return round(self.duration / 60, 2)

    @property
    def is_available(self):
        """Check if service is available (active and artist is available)."""
        return self.is_active and self.artist.is_available
