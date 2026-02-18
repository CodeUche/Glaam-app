# Notifications App

Real-time notification system for GlamConnect using Django Channels and WebSockets.

## Features

- Real-time notifications via WebSocket
- REST API for notification management
- JWT authentication for WebSocket connections
- Celery tasks for background notification delivery
- Support for booking and review notifications
- Artist availability status updates
- Notification statistics and bulk operations

## Architecture

### Components

1. **Models** (`models.py`)
   - Notification model with support for different notification types
   - Related to bookings and users

2. **Serializers** (`serializers.py`)
   - NotificationSerializer: Full notification details
   - NotificationListSerializer: Lightweight list view
   - MarkAsReadSerializer: Bulk mark as read
   - NotificationStatsSerializer: Statistics

3. **Views** (`views.py`)
   - List notifications (paginated)
   - Mark as read (single/bulk/all)
   - Delete notifications
   - Get statistics

4. **Consumers** (`consumers.py`)
   - NotificationConsumer: User notifications
   - ArtistStatusConsumer: Artist availability updates

5. **Middleware** (`middleware.py`)
   - JWT authentication for WebSocket connections

6. **Utils** (`utils.py`)
   - Helper functions for creating and sending notifications
   - Real-time notification delivery

7. **Tasks** (`tasks.py`)
   - Celery tasks for background notification delivery
   - Booking reminders
   - Cleanup old notifications

## API Endpoints

### REST API

All endpoints require JWT authentication.

#### List Notifications
```http
GET /api/v1/notifications/
```

Query parameters:
- `is_read`: Filter by read status (true/false)
- `type`: Filter by notification type
- `booking_id`: Filter by related booking

Response:
```json
{
  "results": [
    {
      "id": "uuid",
      "notification_type": "booking_accepted",
      "title": "Booking Accepted",
      "message": "Your booking has been accepted",
      "is_read": false,
      "created_at": "2026-02-17T10:00:00Z",
      "time_ago": "2 hours ago"
    }
  ],
  "unread_count": 5
}
```

#### Get Single Notification
```http
GET /api/v1/notifications/{id}/
```

#### Mark Single Notification as Read
```http
PATCH /api/v1/notifications/{id}/mark-read/
```

#### Mark All as Read
```http
POST /api/v1/notifications/mark-all-read/
```

#### Bulk Mark as Read
```http
POST /api/v1/notifications/bulk-mark-read/
Content-Type: application/json

{
  "notification_ids": ["uuid1", "uuid2", "uuid3"]
}
```

If `notification_ids` is not provided, all notifications will be marked as read.

#### Get Statistics
```http
GET /api/v1/notifications/stats/
```

Response:
```json
{
  "total": 50,
  "unread": 5,
  "read": 45,
  "by_type": {
    "booking_accepted": 10,
    "booking_reminder": 5,
    "review_received": 3
  }
}
```

#### Delete Notification
```http
DELETE /api/v1/notifications/{id}/
```

#### Clear All Notifications
```http
DELETE /api/v1/notifications/clear-all/
```

#### Clear Read Notifications
```http
DELETE /api/v1/notifications/clear-read/
```

### WebSocket API

#### Connection

Connect to the WebSocket endpoint with JWT token:

```javascript
const token = 'your-jwt-access-token';
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);
```

Or pass via header (if supported by client):
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');
// Set Authorization header: Bearer <token>
```

#### Events from Server

**Connection Established**
```json
{
  "type": "connection.established",
  "message": "Connected to notification service",
  "user_id": "uuid"
}
```

**Unread Count**
```json
{
  "type": "notification.unread_count",
  "count": 5
}
```

**New Notification**
```json
{
  "type": "notification.new",
  "notification": {
    "id": "uuid",
    "type": "booking_accepted",
    "title": "Booking Accepted",
    "message": "Your booking has been accepted",
    "related_booking_id": "uuid",
    "is_read": false,
    "created_at": "2026-02-17T10:00:00Z"
  }
}
```

**Booking Created**
```json
{
  "type": "booking.created",
  "data": {
    "booking_id": "uuid",
    "booking_number": "BK20260217100000ABC123",
    "status": "pending",
    "booking_date": "2026-03-15",
    "start_time": "10:00",
    "artist_name": "Jane Doe",
    "client_name": "John Smith"
  }
}
```

**Booking Accepted**
```json
{
  "type": "booking.accepted",
  "data": {
    "booking_id": "uuid",
    "booking_number": "BK20260217100000ABC123",
    "status": "accepted",
    "message": "Your booking has been accepted"
  }
}
```

**Booking Rejected**
```json
{
  "type": "booking.rejected",
  "data": {
    "booking_id": "uuid",
    "message": "Your booking was declined"
  }
}
```

**Booking Completed**
```json
{
  "type": "booking.completed",
  "data": {
    "booking_id": "uuid",
    "message": "Your booking has been completed"
  }
}
```

**Booking Cancelled**
```json
{
  "type": "booking.cancelled",
  "data": {
    "booking_id": "uuid",
    "message": "Your booking has been cancelled"
  }
}
```

**Booking Reminder**
```json
{
  "type": "booking.reminder",
  "data": {
    "booking_id": "uuid",
    "booking_date": "2026-03-15",
    "start_time": "10:00"
  }
}
```

**Review Received**
```json
{
  "type": "review.received",
  "data": {
    "review_id": "uuid",
    "rating": 5,
    "comment": "Excellent service!",
    "client_name": "John Smith",
    "booking_id": "uuid"
  }
}
```

**Artist Status**
```json
{
  "type": "artist.status",
  "data": {
    "artist_id": "uuid",
    "is_available": true
  }
}
```

#### Client Commands

**Ping/Pong (Connection Health Check)**
```json
// Send
{
  "type": "ping",
  "timestamp": 1234567890
}

// Receive
{
  "type": "pong",
  "timestamp": 1234567890
}
```

**Mark Notification as Read**
```json
{
  "type": "mark_read",
  "notification_id": "uuid"
}
```

**Get Unread Count**
```json
{
  "type": "get_unread_count"
}
```

## Usage Examples

### Backend: Creating Notifications

```python
from apps.notifications.utils import create_notification, send_booking_notification

# Create a simple notification
notification = create_notification(
    user=user,
    notification_type='system',
    title='Welcome to GlamConnect',
    message='Thank you for joining us!',
    send_realtime=True
)

# Create a booking notification
notification = send_booking_notification(
    booking=booking,
    notification_type='booking_accepted',
    recipient_user=client_user
)
```

### Backend: Using Celery Tasks

```python
from apps.notifications.tasks import (
    send_notification_task,
    send_booking_notification_task
)

# Send notification asynchronously
send_notification_task.delay(
    user_id=user.id,
    notification_type='system',
    title='Important Update',
    message='Please check your profile'
)

# Send booking notification asynchronously
send_booking_notification_task.delay(
    booking_id=booking.id,
    notification_type='booking_accepted',
    recipient_user_id=client.id
)
```

### Frontend: WebSocket Connection (JavaScript)

```javascript
class NotificationService {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.ws = new WebSocket(
      `ws://localhost:8000/ws/notifications/?token=${this.token}`
    );

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.stopHeartbeat();
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'connection.established':
        console.log('Connected:', data);
        break;

      case 'notification.new':
        this.showNotification(data.notification);
        break;

      case 'booking.accepted':
        this.handleBookingAccepted(data.data);
        break;

      case 'notification.unread_count':
        this.updateUnreadCount(data.count);
        break;

      default:
        console.log('Unhandled message:', data);
    }
  }

  markAsRead(notificationId) {
    this.send({
      type: 'mark_read',
      notification_id: notificationId
    });
  }

  getUnreadCount() {
    this.send({
      type: 'get_unread_count'
    });
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.send({
        type: 'ping',
        timestamp: Date.now()
      });
    }, 30000); // Every 30 seconds
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
    }
  }

  showNotification(notification) {
    // Implement your notification display logic
    console.log('New notification:', notification);
    // Update UI, show toast, etc.
  }

  handleBookingAccepted(data) {
    // Handle booking acceptance
    console.log('Booking accepted:', data);
    // Update booking status in UI
  }

  updateUnreadCount(count) {
    // Update unread count in UI
    console.log('Unread count:', count);
  }
}

// Usage
const token = localStorage.getItem('access_token');
const notificationService = new NotificationService(token);
notificationService.connect();
```

### Frontend: React Example

```jsx
import { useEffect, useState, useRef } from 'react';

function useNotifications(token) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token) return;

    // Connect to WebSocket
    const ws = new WebSocket(
      `ws://localhost:8000/ws/notifications/?token=${token}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'notification.new':
          setNotifications(prev => [data.notification, ...prev]);
          setUnreadCount(prev => prev + 1);
          break;

        case 'notification.unread_count':
          setUnreadCount(data.count);
          break;

        case 'booking.accepted':
          // Handle booking accepted
          console.log('Booking accepted:', data.data);
          break;
      }
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [token]);

  const markAsRead = (notificationId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'mark_read',
        notification_id: notificationId
      }));
    }
  };

  return { notifications, unreadCount, markAsRead };
}

// Usage in component
function NotificationBell() {
  const token = localStorage.getItem('access_token');
  const { notifications, unreadCount, markAsRead } = useNotifications(token);

  return (
    <div>
      <div className="notification-bell">
        Notifications {unreadCount > 0 && <span>({unreadCount})</span>}
      </div>
      <div className="notification-list">
        {notifications.map(notif => (
          <div key={notif.id} onClick={() => markAsRead(notif.id)}>
            <h4>{notif.title}</h4>
            <p>{notif.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Celery Configuration

Add to `config/celery.py` or wherever you configure Celery Beat:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-booking-reminders-daily': {
        'task': 'notifications.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
    },
    'cleanup-old-notifications': {
        'task': 'notifications.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2 AM
        'kwargs': {'days': 30}
    },
    'resend-failed-notifications': {
        'task': 'notifications.resend_failed_notifications',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}
```

## Testing

### Testing WebSocket Connection

```bash
# Using wscat (install: npm install -g wscat)
wscat -c "ws://localhost:8000/ws/notifications/?token=YOUR_JWT_TOKEN"
```

### Testing with Python

```python
import asyncio
import websockets
import json

async def test_notifications():
    uri = "ws://localhost:8000/ws/notifications/?token=YOUR_JWT_TOKEN"
    async with websockets.connect(uri) as websocket:
        # Receive connection confirmation
        response = await websocket.recv()
        print(f"Received: {response}")

        # Send ping
        await websocket.send(json.dumps({
            "type": "ping",
            "timestamp": 1234567890
        }))

        # Receive pong
        response = await websocket.recv()
        print(f"Received: {response}")

        # Keep connection open
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")

asyncio.run(test_notifications())
```

## Notification Types

- `booking_request`: New booking request (to artist)
- `new_booking`: Booking created confirmation (to client)
- `booking_accepted`: Booking accepted by artist
- `booking_rejected`: Booking rejected by artist
- `booking_completed`: Booking marked as completed
- `booking_cancelled`: Booking cancelled
- `booking_reminder`: Reminder for upcoming booking
- `review_received`: New review received (to artist)
- `system`: System notifications

## Security

- WebSocket connections are authenticated using JWT tokens
- Only authenticated users can connect
- Users can only receive their own notifications
- Rate limiting is applied to REST endpoints
- CORS and allowed hosts are configured

## Deployment Considerations

1. **Redis**: Required for Channel Layers
   ```bash
   # Make sure Redis is running
   redis-server
   ```

2. **Daphne**: ASGI server for production
   ```bash
   daphne -p 8000 config.asgi:application
   ```

3. **Nginx**: Configure WebSocket proxy
   ```nginx
   location /ws/ {
       proxy_pass http://localhost:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
   }
   ```

4. **Celery**: Start workers and beat
   ```bash
   celery -A config worker -l info
   celery -A config beat -l info
   ```

## Troubleshooting

### WebSocket Connection Issues

1. **Check if Redis is running**
   ```bash
   redis-cli ping
   ```

2. **Check Channel Layers configuration in settings.py**

3. **Verify JWT token is valid**

4. **Check CORS and allowed hosts settings**

### No Notifications Received

1. **Check if user is connected**
   - Look for "WebSocket connected" in logs

2. **Verify notification was created in database**

3. **Check Celery worker is running**

4. **Check Channel Layer connection**
   ```python
   from channels.layers import get_channel_layer
   channel_layer = get_channel_layer()
   # Should not be None
   ```

## License

Part of GlamConnect project.
