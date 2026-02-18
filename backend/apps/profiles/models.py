"""
Profile models for clients and makeup artists.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField

User = get_user_model()


class ClientProfile(models.Model):
    """Profile for clients who book makeup services."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    profile_photo = CloudinaryField('image', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    preferred_location = models.CharField(max_length=255, blank=True, null=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles_clientprofile'
        verbose_name = 'Client Profile'
        verbose_name_plural = 'Client Profiles'

    def __str__(self):
        return f"Client: {self.user.full_name}"


class MakeupArtistProfile(models.Model):
    """Profile for makeup artists offering services."""

    SPECIALTY_CHOICES = [
        ('bridal', 'Bridal'),
        ('editorial', 'Editorial'),
        ('natural', 'Natural/Everyday'),
        ('glam', 'Glamour'),
        ('sfx', 'Special Effects'),
        ('airbrush', 'Airbrush'),
        ('theatrical', 'Theatrical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artist_profile')
    profile_photo = CloudinaryField('image', null=True, blank=True)
    bio = models.TextField()
    specialties = ArrayField(
        models.CharField(max_length=50, choices=SPECIALTY_CHOICES),
        default=list,
        blank=True
    )
    years_of_experience = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_available = models.BooleanField(default=True, db_index=True)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        db_index=True
    )
    total_reviews = models.PositiveIntegerField(default=0)
    total_bookings = models.PositiveIntegerField(default=0)
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles_makeupartistprofile'
        verbose_name = 'Makeup Artist Profile'
        verbose_name_plural = 'Makeup Artist Profiles'
        indexes = [
            models.Index(fields=['average_rating', '-created_at']),
            models.Index(fields=['location', 'is_available']),
        ]

    def __str__(self):
        return f"Artist: {self.user.full_name}"

    def update_rating(self):
        """Update average rating based on reviews."""
        from apps.reviews.models import Review
        reviews = Review.objects.filter(artist=self, is_visible=True)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.total_reviews = reviews.count()
            self.save(update_fields=['average_rating', 'total_reviews', 'updated_at'])


class PortfolioImage(models.Model):
    """Portfolio images uploaded by makeup artists."""

    CATEGORY_CHOICES = [
        ('bridal', 'Bridal'),
        ('editorial', 'Editorial'),
        ('natural', 'Natural'),
        ('glam', 'Glamour'),
        ('sfx', 'Special Effects'),
        ('before_after', 'Before & After'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(
        MakeupArtistProfile,
        on_delete=models.CASCADE,
        related_name='portfolio_images'
    )
    image_url = CloudinaryField('image')
    thumbnail_url = CloudinaryField('image', null=True, blank=True)
    caption = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    display_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portfolio_portfolioimage'
        verbose_name = 'Portfolio Image'
        verbose_name_plural = 'Portfolio Images'
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['artist', 'display_order']),
            models.Index(fields=['artist', 'is_featured']),
        ]

    def __str__(self):
        return f"{self.artist.user.full_name} - {self.category}"


class Favorite(models.Model):
    """Client's favorite makeup artists."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    artist = models.ForeignKey(
        MakeupArtistProfile,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites_favorite'
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        unique_together = ['client', 'artist']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]

    def __str__(self):
        return f"{self.client.full_name} favorites {self.artist.user.full_name}"


class Availability(models.Model):
    """Regular weekly availability for makeup artists."""

    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(
        MakeupArtistProfile,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'availability_availability'
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'
        indexes = [
            models.Index(fields=['artist', 'day_of_week', 'is_active']),
        ]

    def __str__(self):
        return f"{self.artist.user.full_name} - {self.get_day_of_week_display()}"


class AvailabilityException(models.Model):
    """Exceptions to regular availability (blocked dates or special availability)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(
        MakeupArtistProfile,
        on_delete=models.CASCADE,
        related_name='availability_exceptions'
    )
    date = models.DateField()
    is_available = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'availability_availabilityexception'
        verbose_name = 'Availability Exception'
        verbose_name_plural = 'Availability Exceptions'
        indexes = [
            models.Index(fields=['artist', 'date']),
        ]

    def __str__(self):
        return f"{self.artist.user.full_name} - {self.date}"
