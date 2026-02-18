"""
Tests for the notifications app.
"""

import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.profiles.models import MakeupArtistProfile
from apps.bookings.models import Booking, Service
from apps.reviews.models import Review
from .models import Notification
from .consumers import NotificationConsumer
from .utils import create_notification, send_booking_notification
from .middleware import JWTAuthMiddlewareStack
from . import routing

User = get_user_model()


class NotificationModelTests(TestCase):
    """Tests for Notification model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='client',
            first_name='Test',
            last_name='User'
        )

    def test_create_notification(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Test Notification',
            message='This is a test notification'
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_sent)

    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message'
        )

        self.assertFalse(notification.is_read)

        notification.mark_as_read()
        notification.refresh_from_db()

        self.assertTrue(notification.is_read)

    def test_notification_str(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message'
        )

        expected_str = f"Test Notification - {self.user.email}"
        self.assertEqual(str(notification), expected_str)


class NotificationAPITests(APITestCase):
    """Tests for Notification API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            role='client',
            first_name='Client',
            last_name='User'
        )

        self.artist_user = User.objects.create_user(
            email='artist@example.com',
            password='testpass123',
            role='artist',
            first_name='Artist',
            last_name='User'
        )

        # Create some notifications
        for i in range(5):
            Notification.objects.create(
                user=self.client_user,
                notification_type='system',
                title=f'Notification {i}',
                message=f'Message {i}'
            )

        # Authenticate
        self.client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_notifications(self):
        """Test listing notifications."""
        response = self.client.get('/api/v1/notifications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIn('unread_count', response.data)

    def test_filter_notifications_by_read_status(self):
        """Test filtering notifications by read status."""
        # Mark some as read
        Notification.objects.filter(user=self.client_user)[:2].update(is_read=True)

        # Filter unread
        response = self.client.get('/api/v1/notifications/?is_read=false')
        self.assertEqual(len(response.data['results']), 3)

        # Filter read
        response = self.client.get('/api/v1/notifications/?is_read=true')
        self.assertEqual(len(response.data['results']), 2)

    def test_mark_notification_as_read(self):
        """Test marking a single notification as read."""
        notification = Notification.objects.filter(user=self.client_user).first()

        response = self.client.patch(
            f'/api/v1/notifications/{notification.id}/mark-read/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        response = self.client.post('/api/v1/notifications/mark-all-read/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

        # Check all are marked as read
        unread_count = Notification.objects.filter(
            user=self.client_user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_bulk_mark_as_read(self):
        """Test bulk marking notifications as read."""
        notifications = list(Notification.objects.filter(user=self.client_user)[:3])
        notification_ids = [str(n.id) for n in notifications]

        response = self.client.post(
            '/api/v1/notifications/bulk-mark-read/',
            {'notification_ids': notification_ids},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_get_notification_stats(self):
        """Test getting notification statistics."""
        # Mark some as read
        Notification.objects.filter(user=self.client_user)[:2].update(is_read=True)

        response = self.client.get('/api/v1/notifications/stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 5)
        self.assertEqual(response.data['read'], 2)
        self.assertEqual(response.data['unread'], 3)

    def test_delete_notification(self):
        """Test deleting a notification."""
        notification = Notification.objects.filter(user=self.client_user).first()

        response = self.client.delete(f'/api/v1/notifications/{notification.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check notification is deleted
        self.assertFalse(
            Notification.objects.filter(id=notification.id).exists()
        )

    def test_clear_all_notifications(self):
        """Test clearing all notifications."""
        response = self.client.delete('/api/v1/notifications/clear-all/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

        # Check all are deleted
        count = Notification.objects.filter(user=self.client_user).count()
        self.assertEqual(count, 0)

    def test_clear_read_notifications(self):
        """Test clearing only read notifications."""
        # Mark 3 as read
        Notification.objects.filter(user=self.client_user)[:3].update(is_read=True)

        response = self.client.delete('/api/v1/notifications/clear-read/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        # Check only unread remain
        count = Notification.objects.filter(user=self.client_user).count()
        self.assertEqual(count, 2)

    def test_user_can_only_see_own_notifications(self):
        """Test that users can only see their own notifications."""
        # Create notification for another user
        Notification.objects.create(
            user=self.artist_user,
            notification_type='system',
            title='Artist Notification',
            message='For artist only'
        )

        response = self.client.get('/api/v1/notifications/')

        # Should only see client's notifications (5), not artist's
        self.assertEqual(len(response.data['results']), 5)


class NotificationUtilsTests(TestCase):
    """Tests for notification utility functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='client',
            first_name='Test',
            last_name='User'
        )

    def test_create_notification_util(self):
        """Test create_notification utility function."""
        notification = create_notification(
            user=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message',
            send_realtime=False  # Don't send via WebSocket in tests
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')

    def test_create_notification_with_invalid_data(self):
        """Test create_notification with invalid data."""
        # Should handle gracefully and return None
        notification = create_notification(
            user=None,  # Invalid
            notification_type='system',
            title='Test',
            message='Test',
            send_realtime=False
        )

        self.assertIsNone(notification)


class NotificationWebSocketTests(TransactionTestCase):
    """Tests for WebSocket consumers."""

    async def test_websocket_connection_without_token(self):
        """Test WebSocket connection without authentication token."""
        application = JWTAuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        )

        communicator = WebsocketCommunicator(application, "/ws/notifications/")

        connected, subprotocol = await communicator.connect()

        # Should reject connection without token
        self.assertFalse(connected)

        await communicator.disconnect()

    # Note: Testing authenticated WebSocket connections requires more complex setup
    # with valid JWT tokens and database transactions. Consider using pytest-asyncio
    # and channels.testing for comprehensive WebSocket testing.


class NotificationSignalTests(TestCase):
    """Tests for notification signals."""

    def setUp(self):
        """Set up test data."""
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            role='client',
            first_name='Client',
            last_name='User'
        )

        self.artist_user = User.objects.create_user(
            email='artist@example.com',
            password='testpass123',
            role='artist',
            first_name='Artist',
            last_name='User'
        )

        self.artist_profile = MakeupArtistProfile.objects.create(
            user=self.artist_user,
            bio='Test artist',
            hourly_rate=100.00,
            location='Test City'
        )

    # Note: Signal tests require actual model creation which may trigger
    # async Celery tasks. Consider mocking Celery tasks for unit tests.
