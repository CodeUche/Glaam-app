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
    'send-booking-reminders': {
        'task': 'apps.bookings.tasks.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    'cleanup-expired-tokens': {
        'task': 'apps.users.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    'update-artist-ratings': {
        'task': 'apps.reviews.tasks.update_artist_ratings',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
    # Notification tasks
    'send-notification-reminders': {
        'task': 'notifications.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    'cleanup-old-notifications': {
        'task': 'notifications.cleanup_old_notifications',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM
        'kwargs': {'days': 30}
    },
    'resend-failed-notifications': {
        'task': 'notifications.resend_failed_notifications',
        'schedule': crontab(minute='*/10'),  # Run every 10 minutes
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
