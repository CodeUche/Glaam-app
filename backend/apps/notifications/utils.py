"""
Utility functions for notifications.
"""

import logging
from typing import Optional, Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()
logger = logging.getLogger(__name__)


def create_notification(
    user,
    notification_type: str,
    title: str,
    message: str,
    related_booking=None,
    send_realtime: bool = True
) -> Optional[Notification]:
    """
    Create a notification and optionally send it via WebSocket.

    Args:
        user: User instance to send notification to
        notification_type: Type of notification (see Notification model choices)
        title: Notification title
        message: Notification message
        related_booking: Optional related Booking instance
        send_realtime: Whether to send via WebSocket immediately

    Returns:
        Created Notification instance or None if failed
    """
    try:
        # Create notification in database
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_booking=related_booking,
        )

        logger.info(f"Created notification {notification.id} for user {user.email}")

        # Send real-time notification via WebSocket
        if send_realtime:
            send_realtime_notification(notification)

        return notification

    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        return None


def send_realtime_notification(notification: Notification):
    """
    Send notification to user via WebSocket.

    Args:
        notification: Notification instance to send
    """
    try:
        channel_layer = get_channel_layer()
        user_channel = f"user_{notification.user.id}"

        # Prepare notification data
        notification_data = {
            'id': str(notification.id),
            'type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'related_booking_id': str(notification.related_booking.id) if notification.related_booking else None,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
        }

        # Send to user's channel
        async_to_sync(channel_layer.group_send)(
            user_channel,
            {
                'type': 'notification.new',
                'notification': notification_data,
            }
        )

        logger.info(f"Sent real-time notification to {user_channel}")

    except Exception as e:
        logger.error(f"Error sending real-time notification: {str(e)}")


def send_booking_notification(
    booking,
    notification_type: str,
    recipient_user,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Send a booking-related notification.

    Args:
        booking: Booking instance
        notification_type: Type of notification
        recipient_user: User to receive the notification
        extra_data: Optional extra data to include
    """
    # Generate title and message based on notification type
    titles_messages = {
        'booking_request': (
            'New Booking Request',
            f'You have a new booking request from {booking.client.full_name} for {booking.booking_date}'
        ),
        'new_booking': (
            'Booking Created',
            f'Your booking with {booking.artist.user.full_name} has been created for {booking.booking_date}'
        ),
        'booking_accepted': (
            'Booking Accepted',
            f'{booking.artist.user.full_name} has accepted your booking for {booking.booking_date}'
        ),
        'booking_rejected': (
            'Booking Rejected',
            f'{booking.artist.user.full_name} has declined your booking request'
        ),
        'booking_completed': (
            'Booking Completed',
            f'Your booking with {booking.artist.user.full_name} has been completed'
        ),
        'booking_cancelled': (
            'Booking Cancelled',
            f'Your booking for {booking.booking_date} has been cancelled'
        ),
        'booking_reminder': (
            'Upcoming Booking Reminder',
            f'Reminder: You have a booking tomorrow at {booking.start_time}'
        ),
    }

    title, message = titles_messages.get(
        notification_type,
        ('Notification', 'You have a new notification')
    )

    # Create notification
    notification = create_notification(
        user=recipient_user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_booking=booking,
        send_realtime=True
    )

    # Send specific booking event via WebSocket
    if notification:
        send_booking_event(booking, notification_type, recipient_user, extra_data)

    return notification


def send_booking_event(
    booking,
    event_type: str,
    recipient_user,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Send a booking event via WebSocket.

    Args:
        booking: Booking instance
        event_type: Type of event (e.g., 'booking.accepted')
        recipient_user: User to receive the event
        extra_data: Optional extra data
    """
    try:
        channel_layer = get_channel_layer()
        user_channel = f"user_{recipient_user.id}"

        # Prepare event data
        data = {
            'booking_id': str(booking.id),
            'booking_number': booking.booking_number,
            'status': booking.status,
            'booking_date': str(booking.booking_date),
            'start_time': str(booking.start_time),
            'artist_name': booking.artist.user.full_name,
            'client_name': booking.client.full_name,
        }

        # Add extra data if provided
        if extra_data:
            data.update(extra_data)

        # Map notification type to event type
        event_type_map = {
            'booking_request': 'booking_created',
            'new_booking': 'booking_created',
            'booking_accepted': 'booking_accepted',
            'booking_rejected': 'booking_rejected',
            'booking_completed': 'booking_completed',
            'booking_cancelled': 'booking_cancelled',
            'booking_reminder': 'booking_reminder',
        }

        channel_event_type = event_type_map.get(event_type, 'booking_created')

        # Send to user's channel
        async_to_sync(channel_layer.group_send)(
            user_channel,
            {
                'type': channel_event_type,
                'data': data,
            }
        )

        logger.info(f"Sent booking event {channel_event_type} to {user_channel}")

    except Exception as e:
        logger.error(f"Error sending booking event: {str(e)}")


def send_review_notification(review, artist_user):
    """
    Send a notification when an artist receives a review.

    Args:
        review: Review instance
        artist_user: User instance of the artist
    """
    title = 'New Review Received'
    message = f'You received a {review.rating}-star review from {review.client.full_name}'

    notification = create_notification(
        user=artist_user,
        notification_type='review_received',
        title=title,
        message=message,
        related_booking=review.booking,
        send_realtime=True
    )

    # Send review event
    if notification:
        try:
            channel_layer = get_channel_layer()
            user_channel = f"user_{artist_user.id}"

            async_to_sync(channel_layer.group_send)(
                user_channel,
                {
                    'type': 'review_received',
                    'data': {
                        'review_id': str(review.id),
                        'rating': review.rating,
                        'comment': review.comment,
                        'client_name': review.client.full_name,
                        'booking_id': str(review.booking.id),
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error sending review event: {str(e)}")

    return notification


def send_system_notification(user, title: str, message: str):
    """
    Send a system notification to a user.

    Args:
        user: User instance
        title: Notification title
        message: Notification message
    """
    return create_notification(
        user=user,
        notification_type='system',
        title=title,
        message=message,
        related_booking=None,
        send_realtime=True
    )


def notify_artist_status_change(artist_id: str, is_available: bool):
    """
    Notify subscribers about artist availability status change.

    Args:
        artist_id: Artist profile ID
        is_available: New availability status
    """
    try:
        channel_layer = get_channel_layer()
        artist_channel = f"artist_status_{artist_id}"

        async_to_sync(channel_layer.group_send)(
            artist_channel,
            {
                'type': 'artist_status_update',
                'data': {
                    'artist_id': str(artist_id),
                    'is_available': is_available,
                }
            }
        )

        logger.info(f"Sent artist status update for artist {artist_id}")

    except Exception as e:
        logger.error(f"Error sending artist status update: {str(e)}")


def bulk_create_notifications(notifications_data: list) -> int:
    """
    Bulk create notifications.

    Args:
        notifications_data: List of dicts with notification data

    Returns:
        Number of notifications created
    """
    try:
        notifications = [
            Notification(
                user=data['user'],
                notification_type=data['notification_type'],
                title=data['title'],
                message=data['message'],
                related_booking=data.get('related_booking'),
            )
            for data in notifications_data
        ]

        created_notifications = Notification.objects.bulk_create(notifications)

        logger.info(f"Bulk created {len(created_notifications)} notifications")

        return len(created_notifications)

    except Exception as e:
        logger.error(f"Error bulk creating notifications: {str(e)}")
        return 0


def get_user_unread_count(user) -> int:
    """
    Get unread notification count for a user.

    Args:
        user: User instance

    Returns:
        Number of unread notifications
    """
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_all_as_read(user):
    """
    Mark all notifications as read for a user.

    Args:
        user: User instance

    Returns:
        Number of notifications marked as read
    """
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)
