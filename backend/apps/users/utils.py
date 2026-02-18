"""
Utility functions for user app.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_verification_email(user):
    """
    Send email verification link to user.
    """
    subject = 'Verify your GlamConnect account'
    message = f'''
    Hi {user.first_name},

    Welcome to GlamConnect! Please verify your email address to complete your registration.

    Verification link: [This would be a real link in production]

    If you didn't create an account, please ignore this email.

    Best regards,
    The GlamConnect Team
    '''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, token):
    """
    Send password reset email to user.
    """
    subject = 'Reset your GlamConnect password'
    message = f'''
    Hi {user.first_name},

    You requested to reset your password for your GlamConnect account.

    Your reset token: {token}

    This link will expire in 24 hours.

    If you didn't request this, please ignore this email.

    Best regards,
    The GlamConnect Team
    '''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def get_client_ip(request):
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
