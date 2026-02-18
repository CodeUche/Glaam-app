"""
Bookings app configuration.
"""

from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """Configuration for the bookings app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bookings'
    verbose_name = 'Bookings'

    def ready(self):
        """Import signals when app is ready."""
        import apps.bookings.signals  # noqa
