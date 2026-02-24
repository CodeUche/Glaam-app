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
def update_artist_rating_on_save(sender, instance, created, **kwargs):
    """
    Update artist rating when a review is created or visibility changes.
    Uses transaction.on_commit to ensure the review is fully saved before updating.
    """
    def trigger_tasks():
        from .tasks import update_artist_rating, check_review_spam

        if created or instance.is_visible:
            logger.info(f"Triggering rating update for artist {instance.artist.id}")
            update_artist_rating.delay(str(instance.artist.id))

        # Run spam detection on new reviews only
        if created:
            logger.info(f"Triggering spam check for review {instance.id}")
            check_review_spam.delay(str(instance.id))

    transaction.on_commit(trigger_tasks)


@receiver(post_delete, sender=Review)
def update_artist_rating_on_delete(sender, instance, **kwargs):
    """Update artist rating when a review is deleted."""
    def trigger_task():
        from .tasks import update_artist_rating
        logger.info(f"Triggering rating update after review deletion for artist {instance.artist.id}")
        update_artist_rating.delay(str(instance.artist.id))

    transaction.on_commit(trigger_task)


@receiver(pre_save, sender=Review)
def capture_pre_save_state(sender, instance, **kwargs):
    """
    Capture the current state of the review before saving.
    Stores old values for comparison in post_save signals.
    """
    if instance.pk:
        try:
            old = Review.objects.get(pk=instance.pk)
            instance._old_is_visible = old.is_visible
            instance._old_artist_response = old.artist_response
        except Review.DoesNotExist:
            instance._old_is_visible = None
            instance._old_artist_response = None
    else:
        instance._old_is_visible = None
        instance._old_artist_response = None


@receiver(post_save, sender=Review)
def handle_visibility_change(sender, instance, created, **kwargs):
    """
    Trigger rating update when review visibility changes.
    """
    if not created and hasattr(instance, '_old_is_visible'):
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
    Uses 'review_received' notification type which is in Notification.choices.
    """
    if created:
        def create_notification():
            try:
                from apps.notifications.models import Notification
                Notification.objects.create(
                    user=instance.artist.user,
                    notification_type='review_received',
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
    Uses pre_save captured state (_old_artist_response) to detect new responses.
    """
    if not created and hasattr(instance, '_old_artist_response'):
        had_response = bool(instance._old_artist_response)
        has_response_now = bool(instance.artist_response)

        # Artist just added a response (was empty, now has content)
        if not had_response and has_response_now:
            def create_notification():
                try:
                    from apps.notifications.models import Notification
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
    Uses pre_save tracking via the booking's own signals to detect status changes.
    """
    if not created and hasattr(instance, '_old_status'):
        from apps.bookings.models import BookingStatus

        was_completed = instance._old_status == BookingStatus.COMPLETED
        is_completed_now = instance.status == BookingStatus.COMPLETED

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
                    f"Scheduled review reminder for booking {instance.booking_number} in 24 hours"
                )

            transaction.on_commit(schedule_reminder)
