"""
Payment models for GlamConnect.

This is a scaffold implementation for Phase 2.
Designed for integration with Stripe, PayPal, or similar providers.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    PROCESSING = 'processing', _('Processing')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')
    REFUNDED = 'refunded', _('Refunded')
    PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')
    CANCELLED = 'cancelled', _('Cancelled')


class PaymentMethod(models.TextChoices):
    CARD = 'card', _('Credit/Debit Card')
    WALLET = 'wallet', _('Digital Wallet')
    BANK = 'bank', _('Bank Transfer')


class Payment(models.Model):
    """
    Payment record for a booking.
    Scaffold for Phase 2 payment integration.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    client = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='payments_made'
    )
    artist = models.ForeignKey(
        'profiles.MakeupArtistProfile',
        on_delete=models.CASCADE,
        related_name='payments_received'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    # Payment gateway fields (scaffold)
    payment_gateway = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    gateway_response = models.JSONField(null=True, blank=True)
    # Refund fields
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_reason = models.TextField(null=True, blank=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['artist', 'status', '-created_at']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} ({self.status})"


class PayoutRecord(models.Model):
    """
    Tracks payouts to artists. Scaffold for Phase 2.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(
        'profiles.MakeupArtistProfile',
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=25, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payout_method = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments_payoutrecord'
        verbose_name = 'Payout Record'
        verbose_name_plural = 'Payout Records'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payout to {self.artist.user.full_name} - {self.amount} {self.currency}"
