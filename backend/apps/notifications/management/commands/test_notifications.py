"""
Management command to test notification system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.notifications.utils import create_notification, send_system_notification
from apps.notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Test notification system by sending test notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of the user to send notification to',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of test notifications to send',
        )

    def handle(self, *args, **options):
        user_email = options.get('user_email')
        count = options.get('count', 1)

        # Get or create a test user
        if user_email:
            try:
                user = User.objects.get(email=user_email)
                self.stdout.write(
                    self.style.SUCCESS(f'Found user: {user.email}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {user_email} not found')
                )
                return
        else:
            # Get the first user or create a test user
            user = User.objects.filter(role='client').first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No client users found. Please specify --user-email')
                )
                return

        # Send test notifications
        self.stdout.write(
            self.style.WARNING(f'Sending {count} test notification(s) to {user.email}...')
        )

        for i in range(count):
            notification = create_notification(
                user=user,
                notification_type='system',
                title=f'Test Notification #{i+1}',
                message=f'This is test notification number {i+1}',
                send_realtime=True
            )

            if notification:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created notification {notification.id}: {notification.title}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create notification #{i+1}')
                )

        # Show summary
        total_notifications = Notification.objects.filter(user=user).count()
        unread_notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Summary ==='))
        self.stdout.write(f'User: {user.email}')
        self.stdout.write(f'Total notifications: {total_notifications}')
        self.stdout.write(f'Unread notifications: {unread_notifications}')
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('Test notifications sent successfully!')
        )
