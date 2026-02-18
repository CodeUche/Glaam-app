"""
WebSocket consumers for real-time notifications.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Handles:
    - Connection/disconnection with JWT authentication
    - User-specific notification channels
    - Real-time notification delivery
    - Online/offline status
    - Booking status updates
    - Review notifications
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')

        # Reject connection if user is not authenticated
        if not self.user or isinstance(self.user, AnonymousUser):
            logger.warning("Unauthenticated WebSocket connection attempt")
            await self.close(code=4001)
            return

        # Create a unique channel for this user
        self.user_channel = f"user_{self.user.id}"

        # Join user's personal notification channel
        await self.channel_layer.group_add(
            self.user_channel,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        logger.info(f"WebSocket connected: {self.user.email} ({self.user_channel})")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'message': 'Connected to notification service',
            'user_id': str(self.user.id),
        }))

        # Mark user as online (optional - for future features)
        await self.mark_user_online(True)

        # Send any unread notification count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notification.unread_count',
            'count': unread_count,
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'user_channel'):
            # Leave user's notification channel
            await self.channel_layer.group_discard(
                self.user_channel,
                self.channel_name
            )

            # Mark user as offline (optional)
            await self.mark_user_online(False)

            logger.info(f"WebSocket disconnected: {self.user.email} (code: {close_code})")

    async def receive(self, text_data):
        """
        Handle messages from WebSocket client.

        Supports commands like:
        - ping/pong for connection health
        - mark_read for marking notifications as read
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp'),
                }))

            elif message_type == 'mark_read':
                # Mark notification as read
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'notification.marked_read',
                        'notification_id': notification_id,
                    }))

            elif message_type == 'get_unread_count':
                # Get current unread count
                count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notification.unread_count',
                    'count': count,
                }))

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from WebSocket: {text_data}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    # Event handlers for different notification types

    async def notification_new(self, event):
        """Handle new notification event."""
        await self.send(text_data=json.dumps({
            'type': 'notification.new',
            'notification': event['notification'],
        }))

    async def booking_created(self, event):
        """Handle booking created notification."""
        await self.send(text_data=json.dumps({
            'type': 'booking.created',
            'data': event['data'],
        }))

    async def booking_accepted(self, event):
        """Handle booking accepted notification."""
        await self.send(text_data=json.dumps({
            'type': 'booking.accepted',
            'data': event['data'],
        }))

    async def booking_rejected(self, event):
        """Handle booking rejected notification."""
        await self.send(text_data=json.dumps({
            'type': 'booking.rejected',
            'data': event['data'],
        }))

    async def booking_completed(self, event):
        """Handle booking completed notification."""
        await self.send(text_data=json.dumps({
            'type': 'booking.completed',
            'data': event['data'],
        }))

    async def booking_cancelled(self, event):
        """Handle booking cancelled notification."""
        await self.send(text_data=json.dumps({
            'type': 'booking.cancelled',
            'data': event['data'],
        }))

    async def booking_reminder(self, event):
        """Handle booking reminder notification."""
        await self.send(text_data=json.dumps({
            'type': 'booking.reminder',
            'data': event['data'],
        }))

    async def review_received(self, event):
        """Handle review received notification."""
        await self.send(text_data=json.dumps({
            'type': 'review.received',
            'data': event['data'],
        }))

    async def artist_status(self, event):
        """Handle artist online/offline status change."""
        await self.send(text_data=json.dumps({
            'type': 'artist.status',
            'data': event['data'],
        }))

    async def system_notification(self, event):
        """Handle system notification."""
        await self.send(text_data=json.dumps({
            'type': 'system.notification',
            'data': event['data'],
        }))

    # Database operations

    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count for the user."""
        from .models import Notification
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        from .models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {self.user.email}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False

    @database_sync_to_async
    def mark_user_online(self, is_online):
        """
        Mark user as online/offline.
        This is a placeholder for future implementation.
        You might want to store this in Redis or cache.
        """
        # TODO: Implement user online status tracking
        # This could be stored in Redis with TTL
        # Or in a separate UserStatus model
        pass


class ArtistStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for artist availability status updates.

    Allows clients to subscribe to artist status changes.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')

        # Reject connection if user is not authenticated
        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return

        # Get artist ID from URL route
        self.artist_id = self.scope['url_route']['kwargs'].get('artist_id')

        if not self.artist_id:
            await self.close(code=4000)
            return

        # Join artist status channel
        self.artist_channel = f"artist_status_{self.artist_id}"

        await self.channel_layer.group_add(
            self.artist_channel,
            self.channel_name
        )

        await self.accept()

        logger.info(f"Artist status WebSocket connected: {self.user.email} -> Artist {self.artist_id}")

        # Send current artist status
        artist_status = await self.get_artist_status()
        await self.send(text_data=json.dumps({
            'type': 'artist.status',
            'artist_id': self.artist_id,
            'is_available': artist_status,
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'artist_channel'):
            await self.channel_layer.group_discard(
                self.artist_channel,
                self.channel_name
            )

    async def artist_status_update(self, event):
        """Handle artist status update event."""
        await self.send(text_data=json.dumps({
            'type': 'artist.status.update',
            'data': event['data'],
        }))

    @database_sync_to_async
    def get_artist_status(self):
        """Get current artist availability status."""
        from apps.profiles.models import MakeupArtistProfile
        try:
            artist = MakeupArtistProfile.objects.get(id=self.artist_id)
            return artist.is_available
        except MakeupArtistProfile.DoesNotExist:
            return False
