"""
Serializers for reviews app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Review
from apps.bookings.models import Booking, BookingStatus
from apps.profiles.models import MakeupArtistProfile

User = get_user_model()


class ReviewClientSerializer(serializers.ModelSerializer):
    """Serializer for client information in reviews."""

    full_name = serializers.CharField(source='full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = fields


class ReviewArtistSerializer(serializers.ModelSerializer):
    """Serializer for artist information in reviews."""

    user_id = serializers.UUIDField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = MakeupArtistProfile
        fields = [
            'id',
            'user_id',
            'full_name',
            'email',
            'profile_photo',
            'average_rating',
            'total_reviews'
        ]
        read_only_fields = fields

    def get_profile_photo(self, obj):
        """Get profile photo URL."""
        if obj.profile_photo:
            return obj.profile_photo.url
        return None


class ReviewBookingSerializer(serializers.ModelSerializer):
    """Minimal booking information for reviews."""

    class Meta:
        model = Booking
        fields = ['id', 'booking_number', 'booking_date', 'status']
        read_only_fields = fields


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews with nested information."""

    client = ReviewClientSerializer(read_only=True)
    artist = ReviewArtistSerializer(read_only=True)
    booking = ReviewBookingSerializer(read_only=True)
    has_response = serializers.BooleanField(read_only=True)
    is_recent = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'booking',
            'client',
            'artist',
            'rating',
            'comment',
            'is_visible',
            'flagged',
            'artist_response',
            'responded_at',
            'has_response',
            'is_recent',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single review retrieval."""

    client = ReviewClientSerializer(read_only=True)
    artist = ReviewArtistSerializer(read_only=True)
    booking = ReviewBookingSerializer(read_only=True)
    has_response = serializers.BooleanField(read_only=True)
    is_recent = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'booking',
            'client',
            'artist',
            'rating',
            'comment',
            'is_visible',
            'flagged',
            'flagged_reason',
            'artist_response',
            'responded_at',
            'has_response',
            'is_recent',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews.
    Validates that only clients with completed bookings can review.
    """

    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.filter(status=BookingStatus.COMPLETED)
    )

    class Meta:
        model = Review
        fields = ['booking', 'rating', 'comment']

    def validate_booking(self, booking):
        """
        Validate booking eligibility for review.

        Rules:
        - Booking must be completed
        - User must be the client of the booking
        - Booking must not already have a review
        """
        user = self.context['request'].user

        # Check if user is the client
        if booking.client != user:
            raise serializers.ValidationError(
                "You can only review bookings that you made."
            )

        # Check if booking is completed
        if booking.status != BookingStatus.COMPLETED:
            raise serializers.ValidationError(
                "Only completed bookings can be reviewed."
            )

        # Check if review already exists
        if hasattr(booking, 'review'):
            raise serializers.ValidationError(
                "This booking has already been reviewed."
            )

        return booking

    def validate_rating(self, rating):
        """Validate rating is between 1 and 5."""
        if rating < 1 or rating > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5 stars."
            )
        return rating

    def validate_comment(self, comment):
        """Validate comment content."""
        if not comment or not comment.strip():
            raise serializers.ValidationError("Review comment cannot be empty.")

        # Basic spam prevention - check for excessive repetition
        words = comment.lower().split()
        if len(words) > 5:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.3:  # More than 70% repetition
                raise serializers.ValidationError(
                    "Review appears to contain spam or excessive repetition."
                )

        # Check minimum length
        if len(comment.strip()) < 10:
            raise serializers.ValidationError(
                "Review comment must be at least 10 characters long."
            )

        # Check maximum length
        if len(comment) > 2000:
            raise serializers.ValidationError(
                "Review comment must not exceed 2000 characters."
            )

        return comment.strip()

    def create(self, validated_data):
        """Create review with auto-populated client and artist."""
        booking = validated_data['booking']
        validated_data['client'] = booking.client
        validated_data['artist'] = booking.artist
        return super().create(validated_data)

    def to_representation(self, instance):
        """Return detailed representation after creation."""
        return ReviewDetailSerializer(instance, context=self.context).data


class ArtistResponseSerializer(serializers.Serializer):
    """Serializer for artist responding to reviews."""

    response = serializers.CharField(
        max_length=1000,
        required=True,
        help_text="Artist's response to the review"
    )

    def validate_response(self, response):
        """Validate response content."""
        if not response or not response.strip():
            raise serializers.ValidationError("Response cannot be empty.")

        # Check minimum length
        if len(response.strip()) < 10:
            raise serializers.ValidationError(
                "Response must be at least 10 characters long."
            )

        # Check maximum length
        if len(response) > 1000:
            raise serializers.ValidationError(
                "Response must not exceed 1000 characters."
            )

        # Basic spam prevention
        words = response.lower().split()
        if len(words) > 5:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.3:
                raise serializers.ValidationError(
                    "Response appears to contain spam or excessive repetition."
                )

        return response.strip()

    def update(self, instance, validated_data):
        """Add or update artist response."""
        instance.add_artist_response(validated_data['response'])
        return instance

    def to_representation(self, instance):
        """Return detailed representation after response."""
        return ReviewDetailSerializer(instance, context=self.context).data


class ReviewModerationSerializer(serializers.Serializer):
    """Serializer for admin moderation actions."""

    action = serializers.ChoiceField(
        choices=['flag', 'unflag', 'hide', 'show'],
        required=True
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Reason for moderation action (required for flag action)"
    )

    def validate(self, data):
        """Validate that reason is provided for flag action."""
        if data['action'] == 'flag' and not data.get('reason'):
            raise serializers.ValidationError({
                'reason': 'Reason is required when flagging a review.'
            })
        return data

    def update(self, instance, validated_data):
        """Perform moderation action."""
        action = validated_data['action']
        reason = validated_data.get('reason')

        if action == 'flag':
            instance.flag_for_moderation(reason=reason)
        elif action == 'unflag':
            instance.unflag()
        elif action == 'hide':
            instance.hide()
        elif action == 'show':
            instance.show()

        return instance

    def to_representation(self, instance):
        """Return detailed representation after moderation."""
        return ReviewDetailSerializer(instance, context=self.context).data


class ReviewStatsSerializer(serializers.Serializer):
    """Serializer for review statistics."""

    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Distribution of ratings (1-5 stars)"
    )
    recent_reviews_count = serializers.IntegerField(
        help_text="Reviews in the last 30 days"
    )
    response_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of reviews with artist response"
    )
