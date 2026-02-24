"""
Utility functions for user app.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature


def generate_email_verification_token(user):
    """
    Generate a signed token for email verification.
    Token is valid for 72 hours. Uses Django's TimestampSigner for security.
    """
    signer = TimestampSigner()
    return signer.sign(str(user.pk))


def verify_email_token(token, max_age_seconds=259200):
    """
    Verify an email verification token.

    Args:
        token: Signed token string
        max_age_seconds: Token validity in seconds (default: 72 hours)

    Returns:
        str: User UUID if valid, None if invalid/expired
    """
    signer = TimestampSigner()
    try:
        user_pk = signer.unsign(token, max_age=max_age_seconds)
        return user_pk
    except (SignatureExpired, BadSignature):
        return None


def send_verification_email(user):
    """
    Send email verification link to user.
    Uses Django signing for secure, time-limited tokens.
    """
    token = generate_email_verification_token(user)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verification_url = f"{frontend_url}/verify-email?token={token}"

    subject = 'Verify your GlamConnect account'
    message = f"""Hi {user.first_name},

Welcome to GlamConnect! Please verify your email address to complete your registration.

Click the link below to verify your email:
{verification_url}

This link will expire in 72 hours.

If you didn't create an account, please ignore this email.

Best regards,
The GlamConnect Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, token):
    """
    Send password reset email to user.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={token}"

    subject = 'Reset your GlamConnect password'
    message = f"""Hi {user.first_name},

You requested to reset your password for your GlamConnect account.

Click the link below to reset your password:
{reset_url}

Or use this token directly: {token}

This link will expire in 24 hours.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
The GlamConnect Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def get_client_ip(request):
    """
    Get client IP address from request, handling proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP (client IP, not proxy IPs)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip
