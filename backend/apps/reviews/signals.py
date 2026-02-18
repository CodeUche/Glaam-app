"""
Signal handlers for reviews app.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import Review

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Review)
def update_artist_rating_on_create(sender, instance, created, **kwargs):
    """
    Update artist rating when a review is created or visibility changes.

    This signal is triggered after a review is saved to:
    - Recalculate artist's average rating
    - Update artist's total review count
    - Trigger spam detection checks
    """
    # Use transaction.on_commit to ensure the review is saved before triggering tasks
    def trigger_tasks():
        from .tasks import update_artist_rating, check_review_spam

        # Always update rating when review is created or visibility changes
        if created or instance.is_visible:
            logger.info(f"Triggering rating update for artist {instance.artist.id}")
            update_artist_rating.delay(str(instance.artist.id))

        # Run spam detection on new reviews
        if created:
            logger.info(f"Triggering spam check for review {instance.id}")
            check_review_spam.delay(str(instance.id))

    transaction.on_commit(trigger_tasks)


@receiver(post_delete, sender=Review)
def update_artist_rating_on_delete(sender, instance, **kwargs):
    """
    Update artist rating when a review is deleted.

    This ensures the artist's rating is recalculated after a review
    is removed from the system.
    """
    def trigger_task():
        from .tasks import update_artist_rating

        logger.info(f"Triggering rating update after review deletion for artist {instance.artist.id}")
        update_artist_rating.delay(str(instance.artist.id))

    transaction.on_commit(trigger_task)


@receiver(pre_save, sender=Review)
def track_visibility_changes(sender, instance, **kwargs):
    """
    Track when review visibility changes to trigger rating updates.

    If a review's visibility changes (hidden/shown), we need to
    recalculate the artist's rating since only visible reviews count.
    """
    if instance.pk:  # Only for existing reviews
        try:
            old_instance = Review.objects.get(pk=instance.pk)
            # Store old visibility state for comparison in post_save
            instance._old_is_visible = old_instance.is_visible
        except Review.DoesNotExist:
            instance._old_is_visible = None


@receiver(post_save, sender=Review)
def handle_visibility_change(sender, instance, created, **kwargs):
    """
    Handle visibility changes by updating artist rating.

    This works in conjunction with the pre_save signal to detect
    when a review's visibility has changed.
    """
    if not created and hasattr(instance, '_old_is_visible'):
        # Check if visibility changed
        if instance._old_is_visible != instance.is_visible:
            def trigger_task():
                from .tasks import update_artist_rating

                logger.info(
                    f"Review visibility changed for review {instance.id}, "
                    f"updating artist {instance.artist.id} rating"
                )
                update_artist_rating.delay(str(instance.artist.id))

            transaction.on_commit(trigger_task)


@receiver(post_save, sender=Review)
def send_notification_to_artist(sender, instance, created, **kwargs):
    """
    Send notification to artist when they receive a new review.

    This creates an in-app notification and could trigger a push
    notification or email if the artist has those enabled.
    """
    if created:
        def create_notification():
            try:
                from apps.notifications.models import Notification

                # Create notification for artist
                Notification.objects.create(
                    user=instance.artist.user,
                    notification_type='new_review',
                    title='New Review Received',
                    message=(
                        f"{instance.client.full_name} left a {instance.rating}-star review "
                        f"for your service. Check it out!"
                    ),
                    related_booking=instance.booking
                )

                logger.info(f"Created notification for artist {instance.artist.user.email} about new review")

            except Exception as e:
                logger.error(f"Error creating notification for new review: {str(e)}")

        transaction.on_commit(create_notification)


@receiver(post_save, sender=Review)
def notify_client_of_artist_response(sender, instance, created, **kwargs):
    """
    Notify client when artist responds to their review.

    This signal detects when an artist adds a response and sends
    a notification to the client who wrote the review.
    """
    if not created and hasattr(instance, '_old_is_visible'):
        # Check if artist just added a response
        try:
            old_instance = Review.objects.get(pk=instance.pk)
            had_response = bool(old_instance.artist_response)
        except Review.DoesNotExist:
            had_response = False

        has_response_now = bool(instance.artist_response)

        # Artist just added a response
        if not had_response and has_response_now:
            def create_notification():
                try:
                    from apps.notifications.models import Notification

                    # Create notification for client
                    Notification.objects.create(
                        user=instance.client,
                        notification_type='review_response',
                        title='Artist Responded to Your Review',
                        message=(
                            f"{instance.artist.user.full_name} responded to your review. "
                            f"See what they said!"
                        ),
                        related_booking=instance.booking
                    )

                    logger.info(
                        f"Created notification for client {instance.client.email} "
                        f"about artist response"
                    )

                except Exception as e:
                    logger.error(f"Error creating notification for artist response: {str(e)}")

            transaction.on_commit(create_notification)


@receiver(post_save, sender='bookings.Booking')
def schedule_review_reminder(sender, instance, created, **kwargs):
    """
    Schedule a review reminder when a booking is completed.

    This signal triggers a delayed task to send a review reminder
    24 hours after the booking is completed.
    """
    from apps.bookings.models import BookingStatus

    # Check if booking was just marked as completed
    if not created:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            was_completed = old_instance.status == BookingStatus.COMPLETED
        except sender.DoesNotExist:
            was_completed = False

        is_completed_now = instance.status == BookingStatus.COMPLETED

        # Booking just completed
        if not was_completed and is_completed_now:
            def schedule_reminder():
                from .tasks import send_review_reminder
                from datetime import timedelta

                # Schedule reminder for 24 hours later
                send_review_reminder.apply_async(
                    args=[str(instance.id)],
                    countdown=int(timedelta(hours=24).total_seconds())
                )

                logger.info(
                    f"Scheduled review reminder for booking {instance.booking_number} "
                    f"in 24 hours"
                )

            transaction.on_commit(schedule_reminder)
