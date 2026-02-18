"""
Celery tasks for bookings app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_booking_notification(self, booking_id, notification_type):
    """
    Send booking notification email and create in-app notification.

    Args:
        booking_id: UUID of the booking
        notification_type: Type of notification (new_booking, booking_accepted, etc.)
    """
    try:
        from .models import Booking
        from apps.notifications.models import Notification

        booking = Booking.objects.select_related(
            'client', 'artist__user', 'service'
        ).get(id=booking_id)

        # Determine recipient and message based on notification type
        if notification_type == 'new_booking':
            recipient = booking.artist.user
            subject = f'New Booking Request - {booking.booking_number}'
            message = (
                f'You have a new booking request from {booking.client.full_name}.\n\n'
                f'Service: {booking.service.name}\n'
                f'Date: {booking.booking_date}\n'
                f'Time: {booking.start_time} - {booking.end_time}\n'
                f'Location: {booking.location}\n'
                f'Total: ${booking.total_price}\n\n'
                f'Please log in to accept or reject this booking.'
            )
            notification_title = 'New Booking Request'
            notification_message = f'{booking.client.full_name} has requested a booking for {booking.booking_date}.'

        elif notification_type == 'booking_accepted':
            recipient = booking.client
            subject = f'Booking Accepted - {booking.booking_number}'
            message = (
                f'Great news! Your booking with {booking.artist.user.full_name} has been accepted.\n\n'
                f'Service: {booking.service.name}\n'
                f'Date: {booking.booking_date}\n'
                f'Time: {booking.start_time} - {booking.end_time}\n'
                f'Location: {booking.location}\n'
                f'Total: ${booking.total_price}\n\n'
                f'We look forward to serving you!'
            )
            notification_title = 'Booking Accepted'
            notification_message = f'{booking.artist.user.full_name} has accepted your booking for {booking.booking_date}.'

        elif notification_type == 'booking_rejected':
            recipient = booking.client
            subject = f'Booking Declined - {booking.booking_number}'
            message = (
                f'Unfortunately, your booking with {booking.artist.user.full_name} has been declined.\n\n'
                f'Service: {booking.service.name}\n'
                f'Date: {booking.booking_date}\n'
                f'Time: {booking.start_time} - {booking.end_time}\n\n'
                f'Please try booking another time slot or choose a different artist.'
            )
            notification_title = 'Booking Declined'
            notification_message = f'{booking.artist.user.full_name} has declined your booking request.'

        elif notification_type == 'booking_completed':
            recipient = booking.client
            subject = f'Booking Completed - {booking.booking_number}'
            message = (
                f'Your booking with {booking.artist.user.full_name} has been marked as completed.\n\n'
                f'Service: {booking.service.name}\n'
                f'Date: {booking.booking_date}\n\n'
                f'We hope you enjoyed the service! Please consider leaving a review.'
            )
            notification_title = 'Booking Completed'
            notification_message = f'Your booking with {booking.artist.user.full_name} is complete. Leave a review!'

        elif notification_type == 'booking_cancelled':
            # Determine who to notify (the other party)
            if booking.cancelled_by == 'client':
                recipient = booking.artist.user
                cancelled_by_name = booking.client.full_name
            else:
                recipient = booking.client
                cancelled_by_name = booking.artist.user.full_name

            subject = f'Booking Cancelled - {booking.booking_number}'
            message = (
                f'The booking has been cancelled by {cancelled_by_name}.\n\n'
                f'Service: {booking.service.name}\n'
                f'Date: {booking.booking_date}\n'
                f'Time: {booking.start_time} - {booking.end_time}\n'
            )
            if booking.cancellation_reason:
                message += f'\nReason: {booking.cancellation_reason}\n'

            notification_title = 'Booking Cancelled'
            notification_message = f'{cancelled_by_name} has cancelled the booking for {booking.booking_date}.'

        elif notification_type == 'booking_reminder':
            recipient = booking.client
            subject = f'Booking Reminder - {booking.booking_number}'
            message = (
                f'This is a reminder for your upcoming booking with {booking.artist.user.full_name}.\n\n'
                f'Service: {booking.service.name}\n'
                f'Date: {booking.booking_date}\n'
                f'Time: {booking.start_time} - {booking.end_time}\n'
                f'Location: {booking.location}\n\n'
                f'See you soon!'
            )
            notification_title = 'Booking Reminder'
            notification_message = f'Reminder: Your booking with {booking.artist.user.full_name} is tomorrow.'

        else:
            logger.error(f'Unknown notification type: {notification_type}')
            return

        # Send email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            logger.info(f'Email sent to {recipient.email} for {notification_type}')
        except Exception as e:
            logger.error(f'Failed to send email: {str(e)}')
            # Retry the task
            raise self.retry(exc=e, countdown=60)

        # Create in-app notification
        try:
            Notification.objects.create(
                user=recipient,
                notification_type=notification_type,
                title=notification_title,
                message=notification_message,
                related_booking=booking
            )
            logger.info(f'In-app notification created for {recipient.email}')
        except Exception as e:
            logger.error(f'Failed to create notification: {str(e)}')

    except Exception as e:
        logger.error(f'Error in send_booking_notification: {str(e)}')
        raise self.retry(exc=e, countdown=60)


@shared_task
def send_booking_reminders():
    """
    Send reminder emails for upcoming bookings (24 hours before).
    This task should be run daily by Celery Beat.
    """
    from datetime import timedelta
    from .models import Booking, BookingStatus

    tomorrow = timezone.now().date() + timedelta(days=1)

    upcoming_bookings = Booking.objects.filter(
        booking_date=tomorrow,
        status=BookingStatus.ACCEPTED
    )

    for booking in upcoming_bookings:
        send_booking_notification.delay(
            booking_id=str(booking.id),
            notification_type='booking_reminder'
        )

    logger.info(f'Sent {upcoming_bookings.count()} booking reminders')


@shared_task
def auto_complete_past_bookings():
    """
    Automatically mark accepted bookings as completed if they are past their end time.
    This task should be run hourly by Celery Beat.
    """
    from datetime import datetime, timedelta
    from .models import Booking, BookingStatus

    # Get bookings from yesterday and earlier that are still accepted
    yesterday = timezone.now().date() - timedelta(days=1)

    past_bookings = Booking.objects.filter(
        booking_date__lte=yesterday,
        status=BookingStatus.ACCEPTED
    )

    count = 0
    for booking in past_bookings:
        try:
            booking.complete()
            count += 1
        except Exception as e:
            logger.error(f'Failed to auto-complete booking {booking.id}: {str(e)}')

    logger.info(f'Auto-completed {count} past bookings')
    return count


@shared_task
def cleanup_old_pending_bookings():
    """
    Cancel pending bookings that are past their booking date.
    This task should be run daily by Celery Beat.
    """
    from .models import Booking, BookingStatus

    today = timezone.now().date()

    old_pending_bookings = Booking.objects.filter(
        booking_date__lt=today,
        status=BookingStatus.PENDING
    )

    count = 0
    for booking in old_pending_bookings:
        try:
            booking.status = BookingStatus.CANCELLED
            booking.cancelled_by = 'system'
            booking.cancellation_reason = 'Automatically cancelled - booking date passed without acceptance'
            booking.cancelled_at = timezone.now()
            booking.save()
            count += 1
        except Exception as e:
            logger.error(f'Failed to cancel old booking {booking.id}: {str(e)}')

    logger.info(f'Cancelled {count} old pending bookings')
    return count


@shared_task(bind=True, max_retries=3)
def send_artist_notification_email(self, artist_email, subject, message):
    """
    Send a generic email to an artist.

    Args:
        artist_email: Email address of the artist
        subject: Email subject
        message: Email message
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[artist_email],
            fail_silently=False,
        )
        logger.info(f'Email sent to {artist_email}')
    except Exception as e:
        logger.error(f'Failed to send email to {artist_email}: {str(e)}')
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_client_notification_email(self, client_email, subject, message):
    """
    Send a generic email to a client.

    Args:
        client_email: Email address of the client
        subject: Email subject
        message: Email message
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[client_email],
            fail_silently=False,
        )
        logger.info(f'Email sent to {client_email}')
    except Exception as e:
        logger.error(f'Failed to send email to {client_email}: {str(e)}')
        raise self.retry(exc=e, countdown=60)
