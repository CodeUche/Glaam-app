"""
Signal handlers for automatic notification creation.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.bookings.models import Booking, BookingStatus
from apps.reviews.models import Review
from .utils import send_booking_notification, send_review_notification
from .tasks import send_booking_notification_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Booking)
def notify_booking_created(sender, instance, created, **kwargs):
    """
    Send notification when a booking is created.
    Notifies the artist about a new booking request.
    """
    if created:
        # Send notification to artist about new booking request
        try:
            send_booking_notification_task.delay(
                booking_id=str(instance.id),
                notification_type='booking_request',
                recipient_user_id=str(instance.artist.user.id)
            )

            # Send confirmation to client
            send_booking_notification_task.delay(
                booking_id=str(instance.id),
                notification_type='new_booking',
                recipient_user_id=str(instance.client.id)
            )

            logger.info(f"Queued notifications for new booking {instance.booking_number}")

        except Exception as e:
            logger.error(f"Error queueing booking notifications: {str(e)}")


@receiver(post_save, sender=Booking)
def notify_booking_status_change(sender, instance, created, **kwargs):
    """
    Send notification when booking status changes.
    """
    if not created and instance.status:
        try:
            # Notify client about status changes
            if instance.status == BookingStatus.ACCEPTED:
                send_booking_notification_task.delay(
                    booking_id=str(instance.id),
                    notification_type='booking_accepted',
                    recipient_user_id=str(instance.client.id)
                )

            elif instance.status == BookingStatus.REJECTED:
                send_booking_notification_task.delay(
                    booking_id=str(instance.id),
                    notification_type='booking_rejected',
                    recipient_user_id=str(instance.client.id)
                )

            elif instance.status == BookingStatus.COMPLETED:
                # Notify both client and artist
                send_booking_notification_task.delay(
                    booking_id=str(instance.id),
                    notification_type='booking_completed',
                    recipient_user_id=str(instance.client.id)
                )
                send_booking_notification_task.delay(
                    booking_id=str(instance.id),
                    notification_type='booking_completed',
                    recipient_user_id=str(instance.artist.user.id)
                )

            elif instance.status == BookingStatus.CANCELLED:
                # Notify the other party (not the one who cancelled)
                if instance.cancelled_by == 'client':
                    recipient = instance.artist.user
                else:
                    recipient = instance.client

                send_booking_notification_task.delay(
                    booking_id=str(instance.id),
                    notification_type='booking_cancelled',
                    recipient_user_id=str(recipient.id)
                )

            logger.info(f"Queued status change notification for booking {instance.booking_number}")

        except Exception as e:
            logger.error(f"Error queueing booking status notification: {str(e)}")


@receiver(post_save, sender=Review)
def notify_review_created(sender, instance, created, **kwargs):
    """
    Send notification when a review is created.
    Notifies the artist about a new review.
    """
    if created:
        try:
            # Send notification to artist
            send_review_notification(
                review=instance,
                artist_user=instance.artist.user
            )

            logger.info(f"Sent review notification for review {instance.id}")

        except Exception as e:
            logger.error(f"Error sending review notification: {str(e)}")
