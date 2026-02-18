"""
Celery tasks for notifications.
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from .models import Notification
from .utils import (
    create_notification,
    send_booking_notification,
    send_realtime_notification,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(name='notifications.send_notification')
def send_notification_task(
    user_id,
    notification_type,
    title,
    message,
    related_booking_id=None
):
    """
    Celery task to send a notification.

    Args:
        user_id: User ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        related_booking_id: Optional booking ID

    Returns:
        Notification ID if successful, None otherwise
    """
    try:
        user = User.objects.get(id=user_id)

        # Get related booking if provided
        related_booking = None
        if related_booking_id:
            from apps.bookings.models import Booking
            related_booking = Booking.objects.get(id=related_booking_id)

        # Create and send notification
        notification = create_notification(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_booking=related_booking,
            send_realtime=True
        )

        if notification:
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save(update_fields=['is_sent', 'sent_at'])

            logger.info(f"Task: Sent notification {notification.id} to user {user.email}")
            return str(notification.id)

        return None

    except User.DoesNotExist:
        logger.error(f"Task: User {user_id} not found")
        return None
    except Exception as e:
        logger.error(f"Task: Error sending notification: {str(e)}")
        return None


@shared_task(name='notifications.send_booking_notification')
def send_booking_notification_task(
    booking_id,
    notification_type,
    recipient_user_id
):
    """
    Celery task to send a booking-related notification.

    Args:
        booking_id: Booking ID
        notification_type: Type of notification
        recipient_user_id: ID of user to receive notification

    Returns:
        Notification ID if successful, None otherwise
    """
    try:
        from apps.bookings.models import Booking

        booking = Booking.objects.select_related(
            'client',
            'artist__user',
            'service'
        ).get(id=booking_id)

        user = User.objects.get(id=recipient_user_id)

        # Send booking notification
        notification = send_booking_notification(
            booking=booking,
            notification_type=notification_type,
            recipient_user=user
        )

        if notification:
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save(update_fields=['is_sent', 'sent_at'])

            logger.info(f"Task: Sent booking notification {notification.id}")
            return str(notification.id)

        return None

    except Exception as e:
        logger.error(f"Task: Error sending booking notification: {str(e)}")
        return None


@shared_task(name='notifications.send_booking_reminders')
def send_booking_reminders():
    """
    Celery task to send reminders for upcoming bookings.
    Should be run daily (e.g., via Celery Beat).

    Sends reminders for bookings happening in 24 hours.
    """
    try:
        from apps.bookings.models import Booking, BookingStatus

        # Get tomorrow's date
        tomorrow = timezone.now().date() + timedelta(days=1)

        # Find accepted bookings for tomorrow
        upcoming_bookings = Booking.objects.filter(
            booking_date=tomorrow,
            status=BookingStatus.ACCEPTED
        ).select_related('client', 'artist__user')

        reminder_count = 0

        for booking in upcoming_bookings:
            # Check if reminder already sent
            existing_reminder = Notification.objects.filter(
                related_booking=booking,
                notification_type='booking_reminder',
                created_at__date=timezone.now().date()
            ).exists()

            if not existing_reminder:
                # Send reminder to client
                client_notification = send_booking_notification(
                    booking=booking,
                    notification_type='booking_reminder',
                    recipient_user=booking.client
                )

                if client_notification:
                    client_notification.is_sent = True
                    client_notification.sent_at = timezone.now()
                    client_notification.save(update_fields=['is_sent', 'sent_at'])
                    reminder_count += 1

                # Send reminder to artist
                artist_notification = send_booking_notification(
                    booking=booking,
                    notification_type='booking_reminder',
                    recipient_user=booking.artist.user
                )

                if artist_notification:
                    artist_notification.is_sent = True
                    artist_notification.sent_at = timezone.now()
                    artist_notification.save(update_fields=['is_sent', 'sent_at'])
                    reminder_count += 1

        logger.info(f"Task: Sent {reminder_count} booking reminders")
        return reminder_count

    except Exception as e:
        logger.error(f"Task: Error sending booking reminders: {str(e)}")
        return 0


@shared_task(name='notifications.cleanup_old_notifications')
def cleanup_old_notifications(days=30):
    """
    Celery task to clean up old read notifications.

    Args:
        days: Delete read notifications older than this many days

    Returns:
        Number of deleted notifications
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        # Delete old read notifications
        deleted_count, _ = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()

        logger.info(f"Task: Deleted {deleted_count} old notifications")
        return deleted_count

    except Exception as e:
        logger.error(f"Task: Error cleaning up notifications: {str(e)}")
        return 0


@shared_task(name='notifications.send_bulk_notifications')
def send_bulk_notifications(notifications_data):
    """
    Celery task to send notifications in bulk.

    Args:
        notifications_data: List of dicts with notification data
            Each dict should contain:
            - user_id
            - notification_type
            - title
            - message
            - related_booking_id (optional)

    Returns:
        Number of notifications sent
    """
    try:
        sent_count = 0

        for data in notifications_data:
            user = User.objects.get(id=data['user_id'])

            # Get related booking if provided
            related_booking = None
            if data.get('related_booking_id'):
                from apps.bookings.models import Booking
                related_booking = Booking.objects.get(id=data['related_booking_id'])

            # Create notification
            notification = create_notification(
                user=user,
                notification_type=data['notification_type'],
                title=data['title'],
                message=data['message'],
                related_booking=related_booking,
                send_realtime=True
            )

            if notification:
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save(update_fields=['is_sent', 'sent_at'])
                sent_count += 1

        logger.info(f"Task: Sent {sent_count} bulk notifications")
        return sent_count

    except Exception as e:
        logger.error(f"Task: Error sending bulk notifications: {str(e)}")
        return 0


@shared_task(name='notifications.resend_failed_notifications')
def resend_failed_notifications():
    """
    Celery task to resend failed notifications.
    Resends notifications that were not marked as sent.

    Returns:
        Number of notifications resent
    """
    try:
        # Find notifications created more than 5 minutes ago but not sent
        cutoff_time = timezone.now() - timedelta(minutes=5)

        failed_notifications = Notification.objects.filter(
            is_sent=False,
            created_at__lt=cutoff_time
        ).select_related('user', 'related_booking')[:100]  # Limit to 100 at a time

        resent_count = 0

        for notification in failed_notifications:
            try:
                # Resend via WebSocket
                send_realtime_notification(notification)

                # Mark as sent
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save(update_fields=['is_sent', 'sent_at'])

                resent_count += 1

            except Exception as e:
                logger.error(f"Task: Error resending notification {notification.id}: {str(e)}")
                continue

        logger.info(f"Task: Resent {resent_count} failed notifications")
        return resent_count

    except Exception as e:
        logger.error(f"Task: Error resending failed notifications: {str(e)}")
        return 0


@shared_task(name='notifications.send_daily_digest')
def send_daily_digest():
    """
    Celery task to send daily digest of unread notifications.
    Should be run once daily via Celery Beat.

    Returns:
        Number of digests sent
    """
    try:
        # Get users with unread notifications
        users_with_unread = Notification.objects.filter(
            is_read=False,
            created_at__gte=timezone.now() - timedelta(days=1)
        ).values_list('user_id', flat=True).distinct()

        digest_count = 0

        for user_id in users_with_unread:
            try:
                user = User.objects.get(id=user_id)

                # Count unread notifications
                unread_count = Notification.objects.filter(
                    user=user,
                    is_read=False
                ).count()

                # Send digest notification
                title = 'Daily Notification Summary'
                message = f'You have {unread_count} unread notification(s)'

                notification = create_notification(
                    user=user,
                    notification_type='system',
                    title=title,
                    message=message,
                    related_booking=None,
                    send_realtime=False  # Don't send via WebSocket for digest
                )

                if notification:
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    notification.save(update_fields=['is_sent', 'sent_at'])
                    digest_count += 1

            except User.DoesNotExist:
                continue
            except Exception as e:
                logger.error(f"Task: Error sending digest to user {user_id}: {str(e)}")
                continue

        logger.info(f"Task: Sent {digest_count} daily digests")
        return digest_count

    except Exception as e:
        logger.error(f"Task: Error sending daily digests: {str(e)}")
        return 0
