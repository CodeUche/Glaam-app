# Notifications Integration Guide

How to integrate the notifications system with other apps in GlamConnect.

## Overview

The notifications app automatically sends notifications for:
- Booking requests, acceptance, rejection, completion, cancellation
- Review submissions
- System announcements

This is achieved through Django signals that listen for changes in the bookings and reviews apps.

## Automatic Integration (via Signals)

Signals are already configured in `apps/notifications/signals.py` and will automatically trigger when:

### Booking Events

**1. New Booking Created**
- Signal: `post_save` on `Booking` model (when `created=True`)
- Notifications sent:
  - To Artist: "New Booking Request" (`booking_request`)
  - To Client: "Booking Created" (`new_booking`)

**2. Booking Accepted**
- Signal: `post_save` on `Booking` model (when `status` changes to `accepted`)
- Notification sent to Client: "Booking Accepted" (`booking_accepted`)

**3. Booking Rejected**
- Signal: `post_save` on `Booking` model (when `status` changes to `rejected`)
- Notification sent to Client: "Booking Rejected" (`booking_rejected`)

**4. Booking Completed**
- Signal: `post_save` on `Booking` model (when `status` changes to `completed`)
- Notifications sent to both Client and Artist: "Booking Completed" (`booking_completed`)

**5. Booking Cancelled**
- Signal: `post_save` on `Booking` model (when `status` changes to `cancelled`)
- Notification sent to the other party (not the canceller)

### Review Events

**1. Review Created**
- Signal: `post_save` on `Review` model (when `created=True`)
- Notification sent to Artist: "New Review Received" (`review_received`)

## Manual Integration

If you need to send notifications manually from your views or other code:

### Example: Booking View

```python
# apps/bookings/views.py
from apps.notifications.utils import send_booking_notification
from apps.notifications.tasks import send_booking_notification_task

class BookingViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=['patch'])
    def accept(self, request, pk=None):
        """Accept a booking."""
        booking = self.get_object()
        booking.accept()

        # Send notification (synchronously)
        send_booking_notification(
            booking=booking,
            notification_type='booking_accepted',
            recipient_user=booking.client
        )

        # OR send asynchronously via Celery (recommended)
        send_booking_notification_task.delay(
            booking_id=str(booking.id),
            notification_type='booking_accepted',
            recipient_user_id=str(booking.client.id)
        )

        return Response({'status': 'accepted'})
```

### Example: Review View

```python
# apps/reviews/views.py
from apps.notifications.utils import send_review_notification

class ReviewViewSet(viewsets.ModelViewSet):

    def perform_create(self, serializer):
        """Create a review and send notification."""
        review = serializer.save()

        # Send notification to artist
        send_review_notification(
            review=review,
            artist_user=review.artist.user
        )
```

### Example: Custom Notification

```python
from apps.notifications.utils import create_notification, send_system_notification

# Send a custom notification
create_notification(
    user=user,
    notification_type='system',
    title='Profile Updated',
    message='Your profile has been successfully updated',
    send_realtime=True
)

# Or use the helper for system notifications
send_system_notification(
    user=user,
    title='Welcome to GlamConnect',
    message='Thank you for joining our platform!'
)
```

## WebSocket Integration in Views

### Broadcasting to Specific Users

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def my_view(request):
    channel_layer = get_channel_layer()

    # Send to specific user's channel
    user_channel = f"user_{user.id}"

    async_to_sync(channel_layer.group_send)(
        user_channel,
        {
            'type': 'notification.new',  # Calls notification_new() in consumer
            'notification': {
                'id': str(notification.id),
                'title': 'Custom Event',
                'message': 'Something happened',
            }
        }
    )
```

### Broadcasting Booking Updates

```python
from apps.notifications.utils import send_booking_event

# In your booking view after status change
send_booking_event(
    booking=booking,
    event_type='booking_accepted',
    recipient_user=booking.client,
    extra_data={
        'custom_field': 'value'
    }
)
```

## Artist Status Updates

When an artist changes their availability:

```python
# apps/profiles/views.py
from apps.notifications.utils import notify_artist_status_change

class ArtistProfileView(generics.UpdateAPIView):

    def perform_update(self, serializer):
        """Update artist profile and notify subscribers."""
        instance = serializer.save()

        # Check if availability changed
        if 'is_available' in serializer.validated_data:
            notify_artist_status_change(
                artist_id=str(instance.id),
                is_available=instance.is_available
            )
```

## Celery Task Integration

### Scheduled Notifications

The following Celery tasks are already configured to run periodically:

**1. Booking Reminders** (Daily at 9 AM)
```python
# Automatically sends reminders for bookings happening tomorrow
# Task: notifications.send_booking_reminders
```

**2. Cleanup Old Notifications** (Daily at 3 AM)
```python
# Deletes read notifications older than 30 days
# Task: notifications.cleanup_old_notifications
```

**3. Resend Failed Notifications** (Every 10 minutes)
```python
# Retries notifications that failed to send
# Task: notifications.resend_failed_notifications
```

### Custom Scheduled Tasks

Add to `config/celery.py`:

```python
app.conf.beat_schedule = {
    'send-weekly-digest': {
        'task': 'notifications.send_weekly_digest',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM
    },
}
```

Then create the task in `apps/notifications/tasks.py`:

```python
@shared_task(name='notifications.send_weekly_digest')
def send_weekly_digest():
    """Send weekly digest to all users."""
    # Your implementation
    pass
```

## Frontend Integration

### React/Next.js Example

```javascript
// hooks/useNotifications.js
import { useEffect, useState } from 'react';

export function useNotifications(token) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    if (!token) return;

    const websocket = new WebSocket(
      `ws://localhost:8000/ws/notifications/?token=${token}`
    );

    websocket.onopen = () => {
      console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'notification.new':
          setNotifications(prev => [data.notification, ...prev]);
          setUnreadCount(prev => prev + 1);
          // Show toast notification
          showToast(data.notification.title, data.notification.message);
          break;

        case 'notification.unread_count':
          setUnreadCount(data.count);
          break;

        case 'booking.accepted':
          // Update booking status in UI
          updateBookingStatus(data.data.booking_id, 'accepted');
          break;

        // Handle other event types...
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket closed');
      // Implement reconnection logic
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [token]);

  const markAsRead = (notificationId) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'mark_read',
        notification_id: notificationId
      }));
    }
  };

  return { notifications, unreadCount, markAsRead };
}

// Component usage
function NotificationBell() {
  const token = localStorage.getItem('access_token');
  const { notifications, unreadCount } = useNotifications(token);

  return (
    <div className="notification-bell">
      <button>
        🔔 {unreadCount > 0 && <span>{unreadCount}</span>}
      </button>
      {/* Render notifications dropdown */}
    </div>
  );
}
```

### Booking Page Integration

```javascript
// pages/bookings/[id].jsx
import { useEffect, useState } from 'react';
import { useNotifications } from '@/hooks/useNotifications';

export default function BookingDetail({ bookingId }) {
  const [booking, setBooking] = useState(null);
  const { notifications } = useNotifications();

  useEffect(() => {
    // Listen for booking updates via WebSocket
    const bookingNotifications = notifications.filter(
      n => n.related_booking_id === bookingId
    );

    if (bookingNotifications.length > 0) {
      const latest = bookingNotifications[0];

      // Update booking status based on notification
      if (latest.notification_type === 'booking_accepted') {
        setBooking(prev => ({ ...prev, status: 'accepted' }));
        showSuccessToast('Your booking has been accepted!');
      }
    }
  }, [notifications, bookingId]);

  return (
    <div>
      <h1>Booking #{booking?.booking_number}</h1>
      <p>Status: {booking?.status}</p>
    </div>
  );
}
```

## Database Queries

### Efficient Notification Queries

```python
# Get user's unread notifications with related data
notifications = Notification.objects.filter(
    user=user,
    is_read=False
).select_related(
    'user',
    'related_booking',
    'related_booking__artist__user'
).order_by('-created_at')[:20]

# Get notification count by type
from django.db.models import Count

stats = Notification.objects.filter(
    user=user
).values('notification_type').annotate(
    count=Count('id')
)

# Mark all booking-related notifications as read
Notification.objects.filter(
    user=user,
    related_booking__isnull=False,
    is_read=False
).update(is_read=True)
```

## Testing Integration

### Testing Signals

```python
# tests.py
from django.test import TestCase
from apps.bookings.models import Booking
from apps.notifications.models import Notification

class BookingNotificationTests(TestCase):

    def test_booking_created_sends_notification(self):
        """Test that creating a booking sends notifications."""
        # Create booking
        booking = Booking.objects.create(...)

        # Check notifications were created
        artist_notification = Notification.objects.get(
            user=booking.artist.user,
            notification_type='booking_request'
        )

        client_notification = Notification.objects.get(
            user=booking.client,
            notification_type='new_booking'
        )

        self.assertIsNotNone(artist_notification)
        self.assertIsNotNone(client_notification)
```

### Testing WebSocket Events

```python
# test_websocket.py
import pytest
from channels.testing import WebsocketCommunicator
from apps.notifications.consumers import NotificationConsumer

@pytest.mark.asyncio
async def test_notification_consumer():
    """Test notification consumer."""
    communicator = WebsocketCommunicator(
        NotificationConsumer.as_asgi(),
        "/ws/notifications/"
    )

    connected, _ = await communicator.connect()
    assert connected

    # Send a message
    await communicator.send_json_to({
        "type": "ping"
    })

    # Receive response
    response = await communicator.receive_json_from()
    assert response["type"] == "pong"

    await communicator.disconnect()
```

## Monitoring and Debugging

### Logging

Check notification logs:

```python
import logging

logger = logging.getLogger(__name__)

# In your view/function
logger.info(f"Sending notification to user {user.email}")
logger.error(f"Failed to send notification: {error}")
```

### Django Admin

View notifications in Django admin:
```
http://localhost:8000/admin/notifications/notification/
```

Filter by:
- User
- Notification type
- Read status
- Date created

### WebSocket Debugging

Browser console:

```javascript
// Check WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/notifications/?token=TOKEN');

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Closed');
```

### Redis Monitoring

```bash
# Monitor Redis commands
redis-cli monitor

# Check keys
redis-cli
> KEYS *
> GET key_name
```

## Best Practices

1. **Always send notifications asynchronously in production**
   ```python
   # Use Celery tasks instead of direct calls
   send_booking_notification_task.delay(...)
   ```

2. **Handle WebSocket disconnections gracefully**
   ```javascript
   // Implement exponential backoff for reconnection
   ```

3. **Don't send too many notifications**
   ```python
   # Group similar notifications
   # Implement rate limiting
   ```

4. **Clean up old notifications regularly**
   ```python
   # Schedule cleanup task via Celery Beat
   ```

5. **Use appropriate notification types**
   ```python
   # Use specific types like 'booking_accepted'
   # instead of generic 'system'
   ```

6. **Index database queries**
   ```python
   # Notifications model already has proper indexes
   # Use select_related() and prefetch_related()
   ```

7. **Validate WebSocket messages**
   ```python
   # Check message type and required fields
   # Sanitize user input
   ```

## Common Issues

### Issue: Notifications not received via WebSocket

**Solution**: Check if user is connected and authenticated:
```python
# In Django shell
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

# Test sending to user
async_to_sync(channel_layer.group_send)(
    "user_USER_ID",
    {"type": "notification.new", "notification": {...}}
)
```

### Issue: Duplicate notifications

**Solution**: Check signals are not registered multiple times:
- Ensure `ready()` method in `apps.py` is called only once
- Use `dispatch_uid` in signal connections

### Issue: Celery tasks not executing

**Solution**: Verify Celery worker is running and tasks are discovered:
```bash
celery -A config inspect registered
```

## Migration from Polling to WebSocket

If you were previously polling for notifications:

```javascript
// Before (polling)
setInterval(() => {
  fetch('/api/v1/notifications/')
    .then(res => res.json())
    .then(data => setNotifications(data.results));
}, 5000);

// After (WebSocket)
const ws = new WebSocket('ws://...');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'notification.new') {
    setNotifications(prev => [data.notification, ...prev]);
  }
};
```

Benefits:
- Real-time updates (instant vs 5 second delay)
- Reduced server load (no constant polling)
- Lower data usage
- Better user experience

## Additional Features to Implement

1. **Email Notifications** - Send email for important notifications
2. **Push Notifications** - Mobile push via FCM/APNs
3. **SMS Notifications** - Critical alerts via Twilio
4. **Notification Preferences** - User settings for notification types
5. **Notification Templates** - HTML email templates
6. **Read Receipts** - Track when notifications are viewed
7. **Notification Groups** - Group related notifications
8. **Mute/Unmute** - Allow users to mute specific notification types

For implementation examples, see the README.md file.
