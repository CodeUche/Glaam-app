"""
Signal handlers for bookings app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Booking, BookingStatus
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Booking)
def capture_booking_pre_save_state(sender, instance, **kwargs):
    """
    Capture the current booking status before saving.
    This is used by other signals (e.g. reviews) to detect status changes.
    """
    if instance.pk:
        try:
            old = Booking.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Booking.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Booking)
def handle_booking_creation(sender, instance, created, **kwargs):
    """
    Handle actions after a booking is created.
    Logs audit trail and increments service booking_count.
    """
    if created:
        logger.info(f'New booking created: {instance.booking_number}')

        # Create audit log entry
        try:
            from apps.users.models import AuditLog
            AuditLog.objects.create(
                user=instance.client,
                action='booking_create',
                resource_type='booking',
                resource_id=instance.id,
                ip_address='0.0.0.0',
                user_agent='system',
                changes={
                    'booking_number': instance.booking_number,
                    'artist_id': str(instance.artist_id),
                    'service_id': str(instance.service_id),
                    'booking_date': str(instance.booking_date),
                    'status': instance.status,
                }
            )
        except Exception as e:
            logger.error(f'Failed to create audit log: {str(e)}')

        # Increment service booking count
        try:
            from django.db.models import F
            type(instance.service).objects.filter(pk=instance.service_id).update(
                booking_count=F('booking_count') + 1
            )
        except Exception as e:
            logger.error(f'Failed to increment service booking_count: {str(e)}')


@receiver(post_save, sender=Booking)
def update_artist_stats(sender, instance, created, **kwargs):
    """Log when booking is completed (total_bookings is updated atomically in complete())."""
    if not created and instance.status == BookingStatus.COMPLETED:
        logger.info(f'Booking {instance.booking_number} completed.')
