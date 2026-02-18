"""
Serializers for service management.
"""

from rest_framework import serializers
from .models import Service, ServiceCategory


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Service model.
    Handles CRUD operations for makeup services.
    """

    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    artist_id = serializers.UUIDField(source='artist.id', read_only=True)
    duration_hours = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        help_text='Duration in hours'
    )
    is_available = serializers.BooleanField(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'artist',
            'artist_id',
            'artist_name',
            'name',
            'description',
            'category',
            'category_display',
            'price',
            'duration',
            'duration_hours',
            'is_active',
            'is_available',
            'booking_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'booking_count', 'created_at', 'updated_at']

    def validate_duration(self, value):
        """Validate that duration is within acceptable range."""
        if value < 15:
            raise serializers.ValidationError(
                "Duration must be at least 15 minutes."
            )
        if value > 480:
            raise serializers.ValidationError(
                "Duration cannot exceed 8 hours (480 minutes)."
            )
        return value

    def validate_price(self, value):
        """Validate that price is positive."""
        if value < 0:
            raise serializers.ValidationError(
                "Price must be a positive value."
            )
        if value > 999999.99:
            raise serializers.ValidationError(
                "Price cannot exceed 999,999.99."
            )
        return value

    def validate_artist(self, value):
        """Validate that the artist profile exists and user is an artist."""
        if not value.user.is_artist:
            raise serializers.ValidationError(
                "Only makeup artists can offer services."
            )
        return value


class ServiceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing services.
    Used for performance optimization in list views.
    """

    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    artist_id = serializers.UUIDField(source='artist.id', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    duration_hours = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Service
        fields = [
            'id',
            'artist_id',
            'artist_name',
            'name',
            'category',
            'category_display',
            'price',
            'duration',
            'duration_hours',
            'is_active',
            'booking_count',
        ]


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating services.
    Excludes artist field as it's set from the request user.
    """

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'category',
            'price',
            'duration',
            'is_active',
        ]
        read_only_fields = ['id']

    def validate_duration(self, value):
        """Validate that duration is within acceptable range."""
        if value < 15:
            raise serializers.ValidationError(
                "Duration must be at least 15 minutes."
            )
        if value > 480:
            raise serializers.ValidationError(
                "Duration cannot exceed 8 hours (480 minutes)."
            )
        return value

    def validate_price(self, value):
        """Validate that price is positive."""
        if value < 0:
            raise serializers.ValidationError(
                "Price must be a positive value."
            )
        if value > 999999.99:
            raise serializers.ValidationError(
                "Price cannot exceed 999,999.99."
            )
        return value

    def create(self, validated_data):
        """Create service with artist from context."""
        artist = self.context['artist']
        validated_data['artist'] = artist
        return super().create(validated_data)
