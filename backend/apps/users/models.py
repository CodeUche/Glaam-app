"""
User models for GlamConnect.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    """User role choices."""
    CLIENT = 'client', _('Client')
    ARTIST = 'artist', _('Makeup Artist')
    ADMIN = 'admin', _('Admin')


class User(AbstractUser):
    """
    Custom user model with role-based access control.

    Extends Django's AbstractUser to add custom fields:
    - UUID primary key for security
    - Role field for RBAC
    - Phone number
    - Email verification
    - Soft delete capability
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    role = models.CharField(
        _('role'),
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CLIENT,
        db_index=True
    )
    is_verified = models.BooleanField(_('verified'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    deleted_at = models.DateTimeField(_('deleted at'), null=True, blank=True)

    # Override username to make it optional (using email as primary identifier)
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['created_at', 'role']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Auto-generate username from email if not provided
        if not self.username:
            self.username = self.email.split('@')[0] + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_client(self):
        """Check if user is a client."""
        return self.role == UserRole.CLIENT

    @property
    def is_artist(self):
        """Check if user is an artist."""
        return self.role == UserRole.ARTIST

    @property
    def is_admin_user(self):
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN or self.is_superuser

    def delete(self, using=None, keep_parents=False, soft=True):
        """
        Soft delete by default, hard delete when soft=False.
        """
        if soft:
            from django.utils import timezone
            self.deleted_at = timezone.now()
            self.is_active = False
            self.save()
        else:
            super().delete(using=using, keep_parents=keep_parents)


class RefreshToken(models.Model):
    """
    Model to track refresh tokens for JWT authentication.
    Allows for token revocation and security auditing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=500, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_refreshtoken'
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'revoked']),
            models.Index(fields=['token', 'revoked', 'expires_at']),
        ]

    def __str__(self):
        return f"Token for {self.user.email} - {'Revoked' if self.revoked else 'Active'}"

    def revoke(self):
        """Revoke this refresh token."""
        from django.utils import timezone
        self.revoked = True
        self.revoked_at = timezone.now()
        self.save()

    @property
    def is_valid(self):
        """Check if token is still valid."""
        from django.utils import timezone
        return not self.revoked and self.expires_at > timezone.now()


class PasswordResetToken(models.Model):
    """
    Model to track password reset tokens.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_passwordresettoken'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_valid(self):
        """Check if token is still valid."""
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()


class AuditLog(models.Model):
    """
    Model to track user actions for security auditing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    resource_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    changes = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_auditlog'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{user_email} - {self.action} at {self.created_at}"
