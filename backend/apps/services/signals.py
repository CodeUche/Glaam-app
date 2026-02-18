"""
Signals for services app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Service


@receiver(post_save, sender=Service)
def service_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a service is created or updated.
    Can be used for logging, notifications, etc.
    """
    if created:
        # Log service creation or send notification
        pass
    else:
        # Log service update
        pass


@receiver(post_delete, sender=Service)
def service_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when a service is deleted.
    Can be used for cleanup, logging, etc.
    """
    # Log service deletion
    pass
