"""
Signal handlers for bookings app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Booking, BookingStatus
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Booking)
def validate_booking_before_save(sender, instance, **kwargs):
    """
    Validate booking before saving.
    Run the model's clean method to ensure data integrity.
    """
    if instance._state.adding:  # Only for new bookings
        instance.full_clean()


@receiver(post_save, sender=Booking)
def handle_booking_creation(sender, instance, created, **kwargs):
    """
    Handle actions after booking is created or updated.
    """
    if created:
        logger.info(f'New booking created: {instance.booking_number}')

        # Log the booking creation
        try:
            from apps.users.models import AuditLog
            AuditLog.objects.create(
                user=instance.client,
                action='booking_create',
                resource_type='booking',
                resource_id=instance.id,
                ip_address='0.0.0.0',  # This would come from request in views
                user_agent='system',
                changes={
                    'booking_number': instance.booking_number,
                    'artist_id': str(instance.artist.id),
                    'service_id': str(instance.service.id),
                    'booking_date': str(instance.booking_date),
                    'status': instance.status,
                }
            )
        except Exception as e:
            logger.error(f'Failed to create audit log: {str(e)}')


@receiver(post_save, sender=Booking)
def update_artist_stats(sender, instance, created, **kwargs):
    """
    Update artist statistics when booking is completed.
    """
    if not created and instance.status == BookingStatus.COMPLETED:
        # The total_bookings is already updated in the complete() method
        logger.info(f'Booking {instance.booking_number} completed. Artist stats updated.')
