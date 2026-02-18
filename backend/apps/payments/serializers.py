"""
Payment serializers - scaffold for Phase 2.
"""

from rest_framework import serializers
from .models import Payment, PayoutRecord


class PaymentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)
    booking_number = serializers.CharField(source='booking.booking_number', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_number', 'client', 'client_name',
            'artist', 'artist_name', 'amount', 'currency', 'payment_method',
            'status', 'transaction_id', 'refund_amount', 'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'id', 'status', 'transaction_id', 'refund_amount',
            'created_at', 'completed_at'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """
    Scaffold for initiating payment.
    In Phase 2, this would integrate with Stripe or a similar provider.
    """
    booking_id = serializers.UUIDField()
    payment_method = serializers.ChoiceField(choices=['card', 'wallet', 'bank'])

    def validate_booking_id(self, value):
        from apps.bookings.models import Booking
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        if hasattr(booking, 'payment'):
            raise serializers.ValidationError("Payment already exists for this booking.")

        if booking.status != 'accepted':
            raise serializers.ValidationError("Can only pay for accepted bookings.")

        return value


class PayoutRecordSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.user.full_name', read_only=True)

    class Meta:
        model = PayoutRecord
        fields = [
            'id', 'artist', 'artist_name', 'amount', 'currency',
            'status', 'payout_method', 'period_start', 'period_end',
            'created_at', 'processed_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'processed_at']
