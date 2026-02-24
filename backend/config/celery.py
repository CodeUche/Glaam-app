"""
Celery configuration for GlamConnect project.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('glamconnect')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Booking lifecycle tasks
    'send-booking-reminders': {
        # Sends reminder emails + in-app notifications for bookings happening tomorrow.
        'task': 'apps.bookings.tasks.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'auto-complete-past-bookings': {
        # Auto-completes accepted bookings whose date has passed.
        'task': 'apps.bookings.tasks.auto_complete_past_bookings',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-old-pending-bookings': {
        # Cancels pending bookings whose date has passed without acceptance.
        'task': 'apps.bookings.tasks.cleanup_old_pending_bookings',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    # User/auth tasks
    'cleanup-expired-tokens': {
        'task': 'apps.users.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Review tasks
    'update-artist-ratings': {
        'task': 'apps.reviews.tasks.update_artist_ratings',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    # Notification maintenance tasks
    'cleanup-old-notifications': {
        # Deletes read notifications older than 30 days.
        'task': 'notifications.cleanup_old_notifications',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        'kwargs': {'days': 30},
    },
    'resend-failed-notifications': {
        # Retries WebSocket delivery for unsent notification records.
        'task': 'notifications.resend_failed_notifications',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
