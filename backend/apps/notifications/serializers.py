"""
Serializers for the notifications app.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    booking_number = serializers.CharField(
        source='related_booking.booking_number',
        read_only=True,
        allow_null=True
    )
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'notification_type',
            'title',
            'message',
            'related_booking',
            'booking_number',
            'is_read',
            'is_sent',
            'sent_at',
            'created_at',
            'time_ago',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'notification_type',
            'title',
            'message',
            'related_booking',
            'booking_number',
            'is_sent',
            'sent_at',
            'created_at',
            'time_ago',
        ]

    def get_time_ago(self, obj):
        """Get human-readable time since notification was created."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for notification lists."""

    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'time_ago',
        ]
        read_only_fields = fields

    def get_time_ago(self, obj):
        """Get human-readable time since notification was created."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If not provided, all will be marked."
    )


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (internal use)."""

    class Meta:
        model = Notification
        fields = [
            'user',
            'notification_type',
            'title',
            'message',
            'related_booking',
        ]

    def validate(self, attrs):
        """Validate notification data."""
        notification_type = attrs.get('notification_type')
        related_booking = attrs.get('related_booking')

        # Ensure booking-related notifications have a related_booking
        booking_types = [
            'booking_request',
            'new_booking',
            'booking_accepted',
            'booking_rejected',
            'booking_completed',
            'booking_cancelled',
            'booking_reminder',
        ]

        if notification_type in booking_types and not related_booking:
            raise serializers.ValidationError({
                'related_booking': f'Notification type "{notification_type}" requires a related booking.'
            })

        return attrs


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics."""

    total = serializers.IntegerField(read_only=True)
    unread = serializers.IntegerField(read_only=True)
    read = serializers.IntegerField(read_only=True)
    by_type = serializers.DictField(read_only=True)
