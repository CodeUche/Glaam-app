"""
Signal handlers for automatic notification creation.

NOTE: Booking notifications (booking_request, booking_accepted, etc.) are sent
via Celery tasks in bookings/views.py which handle both email + in-app notification.
This avoids duplicate notifications from both signals and views.

Review notifications are handled here because reviews don't have a dedicated task
call from views for the artist notification.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)
# Booking signals are intentionally NOT registered here.
# They are triggered via send_booking_notification.delay() in bookings/views.py.
# This single-source approach prevents duplicate in-app notifications.
