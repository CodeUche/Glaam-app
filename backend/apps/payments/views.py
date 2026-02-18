"""
Payment views - scaffold for Phase 2.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum

from .models import Payment, PayoutRecord
from .serializers import PaymentSerializer, PaymentCreateSerializer, PayoutRecordSerializer
from apps.users.permissions import IsClient, IsArtist, IsAdmin


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payment endpoints. Currently read-only scaffold.
    Phase 2 will add payment processing via Stripe/PayPal.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_client:
            return Payment.objects.filter(client=user).select_related('booking', 'artist__user')
        elif user.is_artist:
            return Payment.objects.filter(
                artist=user.artist_profile
            ).select_related('booking', 'client')
        elif user.is_admin_user:
            return Payment.objects.all().select_related('booking', 'client', 'artist__user')
        return Payment.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[IsClient])
    def initiate(self, request):
        """
        Initiate a payment for a booking.
        Scaffold - returns mock success response.
        """
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({
            'message': 'Payment processing is not yet implemented (Phase 2).',
            'status': 'scaffold',
            'booking_id': str(serializer.validated_data['booking_id']),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def summary(self, request):
        """Get payment summary for the current user."""
        user = request.user

        if user.is_client:
            payments = Payment.objects.filter(client=user)
        elif user.is_artist:
            payments = Payment.objects.filter(artist=user.artist_profile)
        else:
            payments = Payment.objects.all()

        total = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        pending = payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'total_paid': float(total),
            'total_pending': float(pending),
            'transaction_count': payments.count(),
        })


class PayoutViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Artist payout records. Read-only scaffold for Phase 2.
    """
    serializer_class = PayoutRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsArtist]

    def get_queryset(self):
        return PayoutRecord.objects.filter(
            artist=self.request.user.artist_profile
        )
