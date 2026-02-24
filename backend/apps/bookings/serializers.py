"""
Serializers for bookings app.
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Booking, BookingStatus
from apps.services.models import Service
from apps.profiles.models import MakeupArtistProfile
from .utils import check_artist_availability


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""

    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    artist_id = serializers.UUIDField(source='artist.id', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'artist', 'artist_name', 'artist_id', 'name',
            'description', 'price', 'duration', 'category',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validate service data."""
        # Ensure artist belongs to the requesting user if creating
        request = self.context.get('request')
        if request and request.method == 'POST':
            user = request.user
            if user.role != 'artist':
                raise serializers.ValidationError(
                    "Only artists can create services."
                )

            # Auto-set artist to the user's artist profile
            try:
                artist_profile = user.artist_profile
                attrs['artist'] = artist_profile
            except MakeupArtistProfile.DoesNotExist:
                raise serializers.ValidationError(
                    "Artist profile not found. Please create your artist profile first."
                )

        return attrs


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings."""

    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_email = serializers.CharField(source='client.email', read_only=True)
    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    artist_photo = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_review = serializers.BooleanField(source='can_be_reviewed', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'client', 'client_name', 'client_email',
            'artist', 'artist_name', 'artist_photo', 'service', 'service_name',
            'booking_date', 'start_time', 'end_time', 'status', 'status_display',
            'location', 'total_price', 'created_at', 'can_review', 'is_upcoming'
        ]
        read_only_fields = ['booking_number', 'created_at']

    def get_artist_photo(self, obj):
        """Get artist profile photo URL."""
        if obj.artist.profile_photo:
            return str(obj.artist.profile_photo.url)
        return None


class BookingDetailSerializer(serializers.ModelSerializer):
    """Serializer for booking details."""

    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_email = serializers.CharField(source='client.email', read_only=True)
    client_phone = serializers.CharField(source='client.phone_number', read_only=True)
    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    artist_email = serializers.CharField(source='artist.user.email', read_only=True)
    artist_phone = serializers.CharField(source='artist.user.phone_number', read_only=True)
    artist_photo = serializers.SerializerMethodField()
    service_details = ServiceSerializer(source='service', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_review = serializers.BooleanField(source='can_be_reviewed', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'client', 'client_name', 'client_email',
            'client_phone', 'artist', 'artist_name', 'artist_email', 'artist_phone',
            'artist_photo', 'service', 'service_details', 'booking_date',
            'start_time', 'end_time', 'status', 'status_display', 'location',
            'client_notes', 'artist_notes', 'cancellation_reason', 'cancelled_by',
            'total_price', 'created_at', 'updated_at', 'accepted_at',
            'completed_at', 'cancelled_at', 'can_review', 'is_upcoming'
        ]
        read_only_fields = [
            'id', 'booking_number', 'created_at', 'updated_at',
            'accepted_at', 'completed_at', 'cancelled_at'
        ]

    def get_artist_photo(self, obj):
        """Get artist profile photo URL."""
        if obj.artist.profile_photo:
            return str(obj.artist.profile_photo.url)
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings."""

    class Meta:
        model = Booking
        fields = [
            'artist', 'service', 'booking_date', 'start_time',
            'end_time', 'location', 'client_notes'
        ]

    def validate(self, attrs):
        """Validate booking creation data."""
        request = self.context.get('request')
        user = request.user if request else None

        # Ensure user is a client
        if not user or user.role != 'client':
            raise serializers.ValidationError(
                "Only clients can create bookings."
            )

        # Validate dates
        booking_date = attrs.get('booking_date')
        if booking_date < timezone.now().date():
            raise serializers.ValidationError({
                'booking_date': 'Booking date cannot be in the past.'
            })

        # Validate times
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })

        # Validate service belongs to artist
        service = attrs.get('service')
        artist = attrs.get('artist')
        if service.artist != artist:
            raise serializers.ValidationError({
                'service': 'This service does not belong to the selected artist.'
            })

        # Validate service is active
        if not service.is_active:
            raise serializers.ValidationError({
                'service': 'This service is no longer available.'
            })

        # Check artist availability
        try:
            is_available = check_artist_availability(
                artist=artist,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time
            )

            if not is_available:
                raise serializers.ValidationError(
                    "The artist is not available at the selected date and time. "
                    "Please choose a different time slot."
                )
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return attrs

    def create(self, validated_data):
        """Create booking with client set to current user."""
        request = self.context.get('request')
        validated_data['client'] = request.user
        validated_data['total_price'] = validated_data['service'].price
        return super().create(validated_data)

    def to_representation(self, instance):
        """Return detailed representation after creation."""
        return BookingDetailSerializer(instance, context=self.context).data


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating booking status."""

    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Validate status update."""
        booking = self.context.get('booking')
        action = self.context.get('action')

        if action == 'accept':
            if booking.status != BookingStatus.PENDING:
                raise serializers.ValidationError(
                    "Only pending bookings can be accepted."
                )
        elif action == 'reject':
            if booking.status != BookingStatus.PENDING:
                raise serializers.ValidationError(
                    "Only pending bookings can be rejected."
                )
        elif action == 'complete':
            if booking.status != BookingStatus.ACCEPTED:
                raise serializers.ValidationError(
                    "Only accepted bookings can be marked as completed."
                )
        elif action == 'cancel':
            if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
                raise serializers.ValidationError(
                    "Cannot cancel completed or already cancelled bookings."
                )

        return attrs


class AvailabilityCheckSerializer(serializers.Serializer):
    """Serializer for checking artist availability."""

    artist_id = serializers.UUIDField()
    booking_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, attrs):
        """Validate availability check data."""
        # Validate date
        booking_date = attrs.get('booking_date')
        if booking_date < timezone.now().date():
            raise serializers.ValidationError({
                'booking_date': 'Date cannot be in the past.'
            })

        # Validate times
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })

        # Validate artist exists
        artist_id = attrs.get('artist_id')
        try:
            artist = MakeupArtistProfile.objects.get(id=artist_id)
            attrs['artist'] = artist
        except MakeupArtistProfile.DoesNotExist:
            raise serializers.ValidationError({
                'artist_id': 'Artist not found.'
            })

        return attrs
