"""
Serializers for the profiles app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import (
    ClientProfile,
    MakeupArtistProfile,
    PortfolioImage,
    Favorite,
    Availability,
    AvailabilityException
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representations."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'first_name', 'last_name', 'phone_number']
        read_only_fields = ['id', 'email']


class ClientProfileSerializer(serializers.ModelSerializer):
    """Serializer for client profiles."""

    user = UserBasicSerializer(read_only=True)
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            'id',
            'user',
            'profile_photo',
            'profile_photo_url',
            'bio',
            'preferred_location',
            'notification_preferences',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'profile_photo': {'write_only': True}
        }

    def get_profile_photo_url(self, obj):
        """Get profile photo URL from Cloudinary field."""
        if obj.profile_photo:
            return obj.profile_photo.url
        return None

    def validate_notification_preferences(self, value):
        """Validate notification preferences structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Notification preferences must be a dictionary.")

        # Define allowed notification types
        allowed_keys = [
            'email_notifications',
            'sms_notifications',
            'booking_updates',
            'promotional_emails',
            'reminder_notifications'
        ]

        # Ensure only valid keys are present
        for key in value.keys():
            if key not in allowed_keys:
                raise serializers.ValidationError(f"Invalid notification preference: {key}")

        return value


class PortfolioImageSerializer(serializers.ModelSerializer):
    """Serializer for portfolio images."""

    image_url_full = serializers.SerializerMethodField()
    thumbnail_url_full = serializers.SerializerMethodField()
    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)

    class Meta:
        model = PortfolioImage
        fields = [
            'id',
            'artist',
            'artist_name',
            'image_url',
            'image_url_full',
            'thumbnail_url',
            'thumbnail_url_full',
            'caption',
            'category',
            'display_order',
            'is_featured',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'image_url': {'write_only': True},
            'thumbnail_url': {'write_only': True},
            'artist': {'required': False}
        }

    def get_image_url_full(self, obj):
        """Get full image URL from Cloudinary field."""
        if obj.image_url:
            return obj.image_url.url
        return None

    def get_thumbnail_url_full(self, obj):
        """Get thumbnail URL from Cloudinary field."""
        if obj.thumbnail_url:
            return obj.thumbnail_url.url
        return None

    def validate_display_order(self, value):
        """Validate display order is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Display order must be non-negative.")
        return value

    def validate(self, attrs):
        """Validate that the user is the artist owner if artist is provided."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user

            # For create operations, set the artist from the logged-in user
            if not self.instance:
                if user.role == 'artist':
                    try:
                        attrs['artist'] = user.artist_profile
                    except MakeupArtistProfile.DoesNotExist:
                        raise serializers.ValidationError(
                            "Artist profile not found for this user."
                        )
                else:
                    raise serializers.ValidationError(
                        "Only makeup artists can upload portfolio images."
                    )
            else:
                # For update operations, verify ownership
                if self.instance.artist.user != user:
                    raise serializers.ValidationError(
                        "You can only modify your own portfolio images."
                    )

        return attrs


class MakeupArtistListSerializer(serializers.ModelSerializer):
    """Optimized serializer for makeup artist listings (list view only)."""

    user = UserBasicSerializer(read_only=True)
    profile_photo_url = serializers.SerializerMethodField()
    featured_images = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    total_favorites = serializers.SerializerMethodField()

    class Meta:
        model = MakeupArtistProfile
        fields = [
            'id',
            'user',
            'profile_photo_url',
            'bio',
            'specialties',
            'years_of_experience',
            'hourly_rate',
            'location',
            'is_available',
            'average_rating',
            'total_reviews',
            'total_bookings',
            'verified',
            'featured_images',
            'is_favorited',
            'total_favorites',
        ]
        read_only_fields = [
            'id',
            'average_rating',
            'total_reviews',
            'total_bookings',
            'verified',
        ]

    def get_profile_photo_url(self, obj):
        """Get profile photo URL from Cloudinary field."""
        if obj.profile_photo:
            return obj.profile_photo.url
        return None

    def get_featured_images(self, obj):
        """Get only featured portfolio images (limited to 3 for listing)."""
        # Check if portfolio_images are prefetched
        if hasattr(obj, '_prefetched_objects_cache') and 'portfolio_images' in obj._prefetched_objects_cache:
            featured = [img for img in obj.portfolio_images.all() if img.is_featured][:3]
        else:
            featured = obj.portfolio_images.filter(is_featured=True)[:3]

        return [
            {
                'id': img.id,
                'image_url': img.image_url.url if img.image_url else None,
                'category': img.category
            }
            for img in featured
        ]

    def get_is_favorited(self, obj):
        """Check if the current user has favorited this artist."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Try to use prefetched data if available
            if hasattr(obj, '_is_favorited'):
                return obj._is_favorited
            return Favorite.objects.filter(
                client=request.user,
                artist=obj
            ).exists()
        return False

    def get_total_favorites(self, obj):
        """Get total number of times this artist has been favorited."""
        # Try to use annotated data if available
        if hasattr(obj, 'favorites_count'):
            return obj.favorites_count
        return obj.favorited_by.count()


class MakeupArtistProfileReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for makeup artist profiles with full details."""

    user = UserBasicSerializer(read_only=True)
    profile_photo_url = serializers.SerializerMethodField()
    portfolio_images = PortfolioImageSerializer(many=True, read_only=True)
    featured_images = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    total_favorites = serializers.SerializerMethodField()
    location_display = serializers.CharField(source='location', read_only=True)

    class Meta:
        model = MakeupArtistProfile
        fields = [
            'id',
            'user',
            'profile_photo',
            'profile_photo_url',
            'bio',
            'specialties',
            'years_of_experience',
            'hourly_rate',
            'location',
            'location_display',
            'latitude',
            'longitude',
            'is_available',
            'average_rating',
            'total_reviews',
            'total_bookings',
            'verified',
            'verification_date',
            'portfolio_images',
            'featured_images',
            'is_favorited',
            'total_favorites',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'average_rating',
            'total_reviews',
            'total_bookings',
            'verified',
            'verification_date',
            'created_at',
            'updated_at'
        ]

    def get_profile_photo_url(self, obj):
        """Get profile photo URL from Cloudinary field."""
        if obj.profile_photo:
            return obj.profile_photo.url
        return None

    def get_featured_images(self, obj):
        """Get only featured portfolio images."""
        featured = obj.portfolio_images.filter(is_featured=True)[:5]
        return PortfolioImageSerializer(featured, many=True).data

    def get_is_favorited(self, obj):
        """Check if the current user has favorited this artist."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                client=request.user,
                artist=obj
            ).exists()
        return False

    def get_total_favorites(self, obj):
        """Get total number of times this artist has been favorited."""
        return obj.favorited_by.count()


class MakeupArtistProfileSerializer(serializers.ModelSerializer):
    """
    Combined serializer for makeup artist profiles.
    Uses different serialization based on action (list vs detail).
    This is the main serializer - MakeupArtistProfileReadSerializer and
    MakeupArtistProfileWriteSerializer are kept for backward compatibility.
    """

    user = UserBasicSerializer(read_only=True)
    profile_photo_url = serializers.SerializerMethodField()
    portfolio_images = PortfolioImageSerializer(many=True, read_only=True)
    featured_images = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    total_favorites = serializers.SerializerMethodField()

    class Meta:
        model = MakeupArtistProfile
        fields = [
            'id',
            'user',
            'profile_photo',
            'profile_photo_url',
            'bio',
            'specialties',
            'years_of_experience',
            'hourly_rate',
            'location',
            'latitude',
            'longitude',
            'is_available',
            'average_rating',
            'total_reviews',
            'total_bookings',
            'verified',
            'verification_date',
            'portfolio_images',
            'featured_images',
            'is_favorited',
            'total_favorites',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'average_rating',
            'total_reviews',
            'total_bookings',
            'verified',
            'verification_date',
            'created_at',
            'updated_at',
            'user'
        ]
        extra_kwargs = {
            'profile_photo': {'write_only': True}
        }

    def get_profile_photo_url(self, obj):
        """Get profile photo URL from Cloudinary field."""
        if obj.profile_photo:
            return obj.profile_photo.url
        return None

    def get_featured_images(self, obj):
        """Get only featured portfolio images."""
        featured = obj.portfolio_images.filter(is_featured=True)[:5]
        return PortfolioImageSerializer(featured, many=True).data

    def get_is_favorited(self, obj):
        """Check if the current user has favorited this artist."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                client=request.user,
                artist=obj
            ).exists()
        return False

    def get_total_favorites(self, obj):
        """Get total number of times this artist has been favorited."""
        if hasattr(obj, 'favorites_count'):
            return obj.favorites_count
        return obj.favorited_by.count()


class MakeupArtistProfileWriteSerializer(serializers.ModelSerializer):
    """Write serializer for makeup artist profiles."""

    class Meta:
        model = MakeupArtistProfile
        fields = [
            'profile_photo',
            'bio',
            'specialties',
            'years_of_experience',
            'hourly_rate',
            'location',
            'latitude',
            'longitude',
            'is_available'
        ]

    def validate_specialties(self, value):
        """Validate specialties list."""
        if not value:
            raise serializers.ValidationError("At least one specialty must be selected.")

        # Check that all specialties are valid choices
        valid_specialties = [choice[0] for choice in MakeupArtistProfile.SPECIALTY_CHOICES]
        for specialty in value:
            if specialty not in valid_specialties:
                raise serializers.ValidationError(f"Invalid specialty: {specialty}")

        # Remove duplicates
        return list(set(value))

    def validate_years_of_experience(self, value):
        """Validate years of experience."""
        if value < 0:
            raise serializers.ValidationError("Years of experience cannot be negative.")
        if value > 50:
            raise serializers.ValidationError("Years of experience cannot exceed 50.")
        return value

    def validate_hourly_rate(self, value):
        """Validate hourly rate."""
        if value <= 0:
            raise serializers.ValidationError("Hourly rate must be greater than zero.")
        if value > 10000:
            raise serializers.ValidationError("Hourly rate seems unreasonably high.")
        return value

    def validate(self, attrs):
        """Validate latitude and longitude together."""
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')

        # If one is provided, both must be provided
        if (latitude is not None) != (longitude is not None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )

        # Validate coordinate ranges
        if latitude is not None:
            if not (-90 <= latitude <= 90):
                raise serializers.ValidationError("Latitude must be between -90 and 90.")

        if longitude is not None:
            if not (-180 <= longitude <= 180):
                raise serializers.ValidationError("Longitude must be between -180 and 180.")

        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorites."""

    artist_details = MakeupArtistProfileReadSerializer(source='artist', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True)

    class Meta:
        model = Favorite
        fields = [
            'id',
            'client',
            'artist',
            'artist_details',
            'client_name',
            'created_at'
        ]
        read_only_fields = ['id', 'client', 'created_at']

    def validate(self, attrs):
        """Validate that the client hasn't already favorited this artist."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            artist = attrs.get('artist')

            # Check if already favorited
            if Favorite.objects.filter(client=user, artist=artist).exists():
                raise serializers.ValidationError(
                    "You have already favorited this artist."
                )

            # Ensure user is not favoriting themselves
            if hasattr(user, 'artist_profile') and user.artist_profile == artist:
                raise serializers.ValidationError(
                    "You cannot favorite your own profile."
                )

        return attrs

    def create(self, validated_data):
        """Create favorite with the current user as client."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['client'] = request.user
        return super().create(validated_data)


class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for artist availability."""

    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Availability
        fields = [
            'id',
            'artist',
            'artist_name',
            'day_of_week',
            'day_name',
            'start_time',
            'end_time',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'artist': {'required': False}
        }

    def validate_day_of_week(self, value):
        """Validate day of week is in valid range."""
        if not 0 <= value <= 6:
            raise serializers.ValidationError("Day of week must be between 0 (Monday) and 6 (Sunday).")
        return value

    def validate(self, attrs):
        """Validate time range and ownership."""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        # Validate time range
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    "Start time must be before end time."
                )

        # Verify ownership
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user

            # For create operations, set the artist from the logged-in user
            if not self.instance:
                if user.role == 'artist':
                    try:
                        attrs['artist'] = user.artist_profile
                    except MakeupArtistProfile.DoesNotExist:
                        raise serializers.ValidationError(
                            "Artist profile not found for this user."
                        )
                else:
                    raise serializers.ValidationError(
                        "Only makeup artists can set availability."
                    )
            else:
                # For update operations, verify ownership
                if self.instance.artist.user != user:
                    raise serializers.ValidationError(
                        "You can only modify your own availability."
                    )

            # Check for overlapping availability on the same day
            artist = attrs.get('artist', self.instance.artist if self.instance else None)
            day_of_week = attrs.get('day_of_week', self.instance.day_of_week if self.instance else None)

            if artist and day_of_week is not None:
                overlapping = Availability.objects.filter(
                    artist=artist,
                    day_of_week=day_of_week,
                    is_active=True
                )

                # Exclude current instance for updates
                if self.instance:
                    overlapping = overlapping.exclude(id=self.instance.id)

                if start_time and end_time:
                    for avail in overlapping:
                        # Check for time overlap
                        if not (end_time <= avail.start_time or start_time >= avail.end_time):
                            raise serializers.ValidationError(
                                f"This availability overlaps with an existing schedule "
                                f"({avail.start_time} - {avail.end_time})."
                            )

        return attrs


class AvailabilityExceptionSerializer(serializers.ModelSerializer):
    """Serializer for availability exceptions."""

    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)

    class Meta:
        model = AvailabilityException
        fields = [
            'id',
            'artist',
            'artist_name',
            'date',
            'is_available',
            'start_time',
            'end_time',
            'reason',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'artist': {'required': False}
        }

    def validate_date(self, value):
        """Validate that the date is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Cannot set availability exception for past dates.")
        return value

    def validate(self, attrs):
        """Validate time range and ownership."""
        is_available = attrs.get('is_available', True)
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        # If marking as available, times are required
        if is_available and (not start_time or not end_time):
            raise serializers.ValidationError(
                "Start time and end time are required when marking a date as available."
            )

        # Validate time range if both provided
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    "Start time must be before end time."
                )

        # Verify ownership
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user

            # For create operations, set the artist from the logged-in user
            if not self.instance:
                if user.role == 'artist':
                    try:
                        attrs['artist'] = user.artist_profile
                    except MakeupArtistProfile.DoesNotExist:
                        raise serializers.ValidationError(
                            "Artist profile not found for this user."
                        )
                else:
                    raise serializers.ValidationError(
                        "Only makeup artists can set availability exceptions."
                    )
            else:
                # For update operations, verify ownership
                if self.instance.artist.user != user:
                    raise serializers.ValidationError(
                        "You can only modify your own availability exceptions."
                    )

        return attrs
