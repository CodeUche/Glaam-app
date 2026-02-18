"""
Signal handlers for user app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create profile based on user role when user is created.
    Import models lazily to avoid circular import at startup.
    """
    if created:
        # Late import avoids circular dependency: users → profiles → users
        from apps.profiles.models import ClientProfile, MakeupArtistProfile
        if instance.is_client:
            ClientProfile.objects.get_or_create(user=instance)
        elif instance.is_artist:
            MakeupArtistProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'bio': '',
                    'location': '',
                    'hourly_rate': 0,
                }
            )
