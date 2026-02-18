"""
Notification models for GlamConnect.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """In-app notifications for users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('booking_request', 'Booking Request'),
            ('new_booking', 'New Booking'),
            ('booking_accepted', 'Booking Accepted'),
            ('booking_rejected', 'Booking Rejected'),
            ('booking_completed', 'Booking Completed'),
            ('booking_cancelled', 'Booking Cancelled'),
            ('booking_reminder', 'Booking Reminder'),
            ('review_received', 'Review Received'),
            ('system', 'System'),
        ]
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False, db_index=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['related_booking']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])
