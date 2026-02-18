"""
Celery tasks for reviews app.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_artist_rating(self, artist_id):
    """
    Update artist's average rating and total review count.

    This task is triggered when:
    - A new review is created
    - A review is deleted
    - A review's visibility changes
    - Scheduled periodic update (every 30 minutes)

    Args:
        artist_id (str): UUID of the artist profile

    Returns:
        dict: Updated rating information
    """
    try:
        from apps.profiles.models import MakeupArtistProfile
        from .models import Review

        artist = MakeupArtistProfile.objects.get(id=artist_id)

        # Get all visible reviews for this artist
        reviews = Review.objects.filter(
            artist=artist,
            is_visible=True
        )

        total_reviews = reviews.count()

        if total_reviews > 0:
            # Calculate average rating
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            artist.average_rating = round(avg_rating, 2)
            artist.total_reviews = total_reviews
        else:
            # No reviews, reset to defaults
            artist.average_rating = 0.0
            artist.total_reviews = 0

        artist.save(update_fields=['average_rating', 'total_reviews', 'updated_at'])

        logger.info(
            f"Updated rating for artist {artist.user.email}: "
            f"{artist.average_rating} ({artist.total_reviews} reviews)"
        )

        return {
            'artist_id': str(artist_id),
            'average_rating': float(artist.average_rating),
            'total_reviews': artist.total_reviews
        }

    except Exception as exc:
        logger.error(f"Error updating artist rating for {artist_id}: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def update_artist_ratings(self):
    """
    Periodic task to update all artists' ratings.

    This is a scheduled task that runs every 30 minutes to ensure
    all ratings are up to date. It's a safety net in case individual
    updates fail.

    Returns:
        dict: Summary of updates
    """
    try:
        from apps.profiles.models import MakeupArtistProfile
        from .models import Review

        artists = MakeupArtistProfile.objects.all()
        updated_count = 0

        for artist in artists:
            # Get visible reviews
            reviews = Review.objects.filter(
                artist=artist,
                is_visible=True
            )

            total_reviews = reviews.count()
            old_rating = artist.average_rating

            if total_reviews > 0:
                avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
                artist.average_rating = round(avg_rating, 2)
                artist.total_reviews = total_reviews
            else:
                artist.average_rating = 0.0
                artist.total_reviews = 0

            # Only save if changed
            if artist.average_rating != old_rating or artist.total_reviews != total_reviews:
                artist.save(update_fields=['average_rating', 'total_reviews', 'updated_at'])
                updated_count += 1

        logger.info(f"Updated ratings for {updated_count} artists")

        return {
            'total_artists': artists.count(),
            'updated_count': updated_count
        }

    except Exception as exc:
        logger.error(f"Error in bulk rating update: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def send_review_reminder(self, booking_id):
    """
    Send a review reminder to client after completed booking.

    This task is triggered when a booking is marked as completed.
    It sends a reminder email after 24 hours if no review has been submitted.

    Args:
        booking_id (str): UUID of the completed booking

    Returns:
        dict: Result of the reminder
    """
    try:
        from apps.bookings.models import Booking, BookingStatus
        from apps.notifications.models import Notification
        from django.core.mail import send_mail
        from django.conf import settings

        booking = Booking.objects.select_related('client', 'artist__user').get(id=booking_id)

        # Check if booking is still completed
        if booking.status != BookingStatus.COMPLETED:
            logger.info(f"Booking {booking_id} is no longer completed, skipping reminder")
            return {'status': 'skipped', 'reason': 'booking not completed'}

        # Check if review already exists
        if hasattr(booking, 'review'):
            logger.info(f"Booking {booking_id} already has a review, skipping reminder")
            return {'status': 'skipped', 'reason': 'review already exists'}

        # Create in-app notification
        Notification.objects.create(
            user=booking.client,
            notification_type='review_reminder',
            title='Leave a Review',
            message=(
                f"How was your experience with {booking.artist.user.full_name}? "
                f"Share your feedback to help others make informed decisions."
            ),
            related_booking=booking
        )

        # Send email reminder
        subject = f"Share your experience with {booking.artist.user.full_name}"
        message = f"""
        Hi {booking.client.first_name},

        We hope you enjoyed your makeup session with {booking.artist.user.full_name}!

        Your feedback is valuable and helps other clients make informed decisions.
        It only takes a minute to leave a review.

        Booking Details:
        - Service: {booking.service.name}
        - Date: {booking.booking_date}
        - Booking Number: {booking.booking_number}

        Thank you for using GlamConnect!

        Best regards,
        The GlamConnect Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.client.email],
            fail_silently=False,
        )

        logger.info(f"Sent review reminder for booking {booking_id} to {booking.client.email}")

        return {
            'status': 'sent',
            'booking_id': str(booking_id),
            'client_email': booking.client.email
        }

    except Exception as exc:
        logger.error(f"Error sending review reminder for booking {booking_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True)
def send_review_reminders_batch(self):
    """
    Batch task to send review reminders for completed bookings without reviews.

    This scheduled task runs daily to check for completed bookings from
    the previous day that don't have reviews yet.

    Returns:
        dict: Summary of reminders sent
    """
    try:
        from apps.bookings.models import Booking, BookingStatus

        # Get completed bookings from 24 hours ago
        yesterday = timezone.now() - timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Find completed bookings without reviews
        bookings = Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            completed_at__range=(start_of_yesterday, end_of_yesterday),
            review__isnull=True  # No review exists
        ).select_related('client', 'artist__user')

        sent_count = 0
        for booking in bookings:
            # Queue individual reminder task
            send_review_reminder.delay(str(booking.id))
            sent_count += 1

        logger.info(f"Queued {sent_count} review reminders")

        return {
            'total_bookings': bookings.count(),
            'reminders_sent': sent_count
        }

    except Exception as exc:
        logger.error(f"Error in batch review reminders: {str(exc)}")
        # Don't retry batch tasks
        return {'error': str(exc)}


@shared_task(bind=True, max_retries=3)
def check_review_spam(self, review_id):
    """
    Advanced spam detection for reviews.

    This task performs more intensive spam checks that shouldn't
    block the review creation process.

    Args:
        review_id (str): UUID of the review to check

    Returns:
        dict: Spam check results
    """
    try:
        from .models import Review

        review = Review.objects.get(id=review_id)

        spam_indicators = []

        # Check for excessive capitalization
        if review.comment.isupper() and len(review.comment) > 20:
            spam_indicators.append('excessive_caps')

        # Check for suspicious patterns (e.g., URLs, emails)
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        if re.search(url_pattern, review.comment):
            spam_indicators.append('contains_url')

        if re.search(email_pattern, review.comment):
            spam_indicators.append('contains_email')

        # Check for duplicate recent reviews from same user
        from datetime import timedelta
        recent_reviews = Review.objects.filter(
            client=review.client,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).exclude(id=review.id)

        if recent_reviews.count() > 3:
            spam_indicators.append('rapid_submission')

        # If spam indicators found, flag for review
        if spam_indicators:
            review.flag_for_moderation(
                reason=f"Automated spam detection: {', '.join(spam_indicators)}"
            )
            logger.warning(
                f"Review {review_id} flagged for spam: {', '.join(spam_indicators)}"
            )

        return {
            'review_id': str(review_id),
            'spam_indicators': spam_indicators,
            'flagged': len(spam_indicators) > 0
        }

    except Exception as exc:
        logger.error(f"Error checking review spam for {review_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
