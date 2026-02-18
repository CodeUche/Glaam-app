"""
Celery tasks for user app.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .utils import send_verification_email, send_password_reset_email
from .models import RefreshToken

User = get_user_model()


@shared_task
def send_verification_email_task(user_id):
    """
    Send verification email asynchronously.
    """
    try:
        user = User.objects.get(id=user_id)
        send_verification_email(user)
        return f"Verification email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with id {user_id} not found"


@shared_task
def send_password_reset_email_task(user_id, token):
    """
    Send password reset email asynchronously.
    """
    try:
        user = User.objects.get(id=user_id)
        send_password_reset_email(user, token)
        return f"Password reset email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with id {user_id} not found"


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired refresh tokens.
    Run daily via Celery beat.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = RefreshToken.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]

    return f"Deleted {deleted_count} expired tokens"


@shared_task
def cleanup_inactive_users():
    """
    Clean up unverified users after 7 days.
    """
    cutoff_date = timezone.now() - timedelta(days=7)
    deleted_count = User.objects.filter(
        is_verified=False,
        created_at__lt=cutoff_date
    ).delete()[0]

    return f"Deleted {deleted_count} inactive users"
