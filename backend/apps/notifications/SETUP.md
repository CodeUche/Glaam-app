# Notifications App Setup Guide

Complete setup instructions for the GlamConnect notifications system.

## Prerequisites

- Django 5.0+
- Django Channels 4.0+
- Redis (for Channel Layers and Celery)
- Celery 5.3+
- PostgreSQL (recommended)

## Installation Steps

### 1. Verify Dependencies

All required dependencies should already be in `requirements.txt`:

```bash
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0
celery==5.3.6
redis==5.0.1
django-redis==5.4.0
```

If not installed:
```bash
pip install -r requirements.txt
```

### 2. Configure Settings

The following settings should already be configured in `config/settings.py`:

#### Channel Layers (for WebSocket)
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('CHANNEL_LAYERS_HOST', default='redis://localhost:6379/3')],
        },
    },
}
```

#### ASGI Application
```python
ASGI_APPLICATION = 'config.asgi.application'
```

#### Celery Configuration
```python
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
```

### 3. Environment Variables

Add to your `.env` file:

```bash
# Redis
REDIS_URL=redis://localhost:6379/0
CHANNEL_LAYERS_HOST=redis://localhost:6379/3

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 4. Database Migrations

Run migrations to create notification tables:

```bash
python manage.py makemigrations notifications
python manage.py migrate notifications
```

### 5. Start Redis

Make sure Redis is running:

```bash
# On Linux/Mac
redis-server

# On Windows (if using WSL)
sudo service redis-server start

# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### 6. Test Channel Layers

Verify Channel Layers are working:

```bash
python manage.py shell
```

```python
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print(channel_layer)  # Should not be None

# Test sending a message
from asgiref.sync import async_to_sync
async_to_sync(channel_layer.group_send)(
    "test_group",
    {"type": "test.message", "text": "Hello"}
)
```

### 7. Start Celery Workers

In separate terminal windows:

#### Start Celery Worker
```bash
celery -A config worker -l info
```

#### Start Celery Beat (for scheduled tasks)
```bash
celery -A config beat -l info
```

### 8. Start Development Server

#### Option A: Using Django's runserver (for testing only)
```bash
python manage.py runserver
```

#### Option B: Using Daphne (ASGI server, recommended)
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

## Verification

### Test REST API

1. **Get JWT Token**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

2. **List Notifications**
```bash
curl -X GET http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

3. **Get Statistics**
```bash
curl -X GET http://localhost:8000/api/v1/notifications/stats/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test WebSocket Connection

#### Using wscat (Node.js tool)
```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/ws/notifications/?token=YOUR_JWT_TOKEN"

# You should receive a connection confirmation message
```

#### Using Python
```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/ws/notifications/?token=YOUR_JWT_TOKEN"
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        message = await websocket.recv()
        print(f"Received: {message}")

        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))

        # Receive pong
        message = await websocket.recv()
        print(f"Received: {message}")

asyncio.run(test())
```

### Test Notifications

#### Using Django Shell
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.notifications.utils import create_notification

User = get_user_model()
user = User.objects.first()

# Create a test notification
notification = create_notification(
    user=user,
    notification_type='system',
    title='Test Notification',
    message='This is a test',
    send_realtime=True
)

print(f"Created notification: {notification.id}")
```

#### Using Management Command
```bash
python manage.py test_notifications --user-email user@example.com --count 5
```

### Test Celery Tasks

```bash
python manage.py shell
```

```python
from apps.notifications.tasks import send_notification_task
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# Queue a notification task
result = send_notification_task.delay(
    user_id=str(user.id),
    notification_type='system',
    title='Celery Test',
    message='Testing Celery task'
)

print(f"Task ID: {result.id}")
print(f"Task State: {result.state}")
```

## Troubleshooting

### WebSocket Connection Issues

**Problem**: WebSocket connections fail or are rejected

**Solutions**:
1. Check Redis is running: `redis-cli ping`
2. Verify JWT token is valid and not expired
3. Check ASGI application is running (use Daphne, not runserver)
4. Check Channel Layers configuration
5. Look for errors in server logs

**Check Channel Layer Connection**:
```python
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print(channel_layer)  # Should not be None
```

### No Notifications Received

**Problem**: Notifications are created but not received via WebSocket

**Solutions**:
1. Check if WebSocket is connected
2. Verify user is authenticated
3. Check Celery worker is running
4. Look for errors in Celery logs
5. Check notification was created: `Notification.objects.all()`

### Celery Tasks Not Running

**Problem**: Celery tasks are queued but not executing

**Solutions**:
1. Make sure Celery worker is running: `celery -A config worker -l info`
2. Check Redis connection
3. Verify task names are correct in `tasks.py`
4. Check Celery logs for errors
5. Test Redis connection:
```bash
redis-cli
> PING
PONG
> KEYS *
```

### Database Migration Issues

**Problem**: Migration errors for notifications app

**Solutions**:
1. Check dependencies are installed
2. Make sure all apps are in INSTALLED_APPS
3. Run migrations in order:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Import Errors

**Problem**: ImportError or ModuleNotFoundError

**Solutions**:
1. Check all `__init__.py` files exist
2. Verify app is in INSTALLED_APPS
3. Make sure virtual environment is activated
4. Reinstall requirements: `pip install -r requirements.txt`

## Production Deployment

### 1. Use Daphne or Uvicorn

```bash
# Daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

### 2. Supervisor Configuration

Create `/etc/supervisor/conf.d/glamconnect.conf`:

```ini
[program:glamconnect_daphne]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 config.asgi:application
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/glamconnect/daphne.log

[program:glamconnect_celery_worker]
command=/path/to/venv/bin/celery -A config worker -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/glamconnect/celery_worker.log

[program:glamconnect_celery_beat]
command=/path/to/venv/bin/celery -A config beat -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/glamconnect/celery_beat.log
```

### 3. Nginx Configuration

Add WebSocket support to Nginx:

```nginx
upstream glamconnect {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # WebSocket configuration
    location /ws/ {
        proxy_pass http://glamconnect;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # Regular HTTP
    location / {
        proxy_pass http://glamconnect;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4. SSL/TLS for WSS

For secure WebSocket connections (wss://):

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /ws/ {
        proxy_pass http://glamconnect;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        # ... other proxy settings
    }
}
```

### 5. Redis Persistence

Configure Redis for persistence in production:

```bash
# /etc/redis/redis.conf
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
```

### 6. Monitoring

Monitor Celery tasks:

```bash
# Flower (Celery monitoring tool)
pip install flower
celery -A config flower --port=5555
```

## Performance Optimization

### 1. Connection Pooling

Use connection pooling for Redis:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
    }
}
```

### 2. Message Expiry

Set expiry on channel messages:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'expiry': 60,  # Messages expire after 60 seconds
        },
    },
}
```

### 3. Celery Optimization

```python
# Celery settings
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_COMPRESSION = 'gzip'
```

## Security Considerations

1. **JWT Token Security**
   - Use short-lived access tokens (15 minutes)
   - Implement token refresh mechanism
   - Validate tokens on every WebSocket message

2. **Rate Limiting**
   - Limit WebSocket connections per user
   - Rate limit REST API endpoints
   - Implement connection throttling

3. **Input Validation**
   - Validate all WebSocket messages
   - Sanitize notification content
   - Prevent XSS in notification messages

4. **CORS Configuration**
   - Only allow trusted origins
   - Configure ALLOWED_HOSTS properly

## Support

For issues or questions:
- Check logs: `tail -f logs/django.log`
- Check Celery logs
- Review Redis logs: `redis-cli monitor`
- Check WebSocket connection in browser console

## Next Steps

1. Integrate with frontend (React/Next.js)
2. Add push notifications (FCM/APNs)
3. Implement email notifications
4. Add SMS notifications (Twilio)
5. Create notification preferences UI
6. Add notification sound/visual alerts
