# Bookings App Setup Guide

## Installation Steps

### 1. Run Migrations

The bookings app includes models for `Service` and `Booking`. Create and run migrations:

```bash
cd c:\Users\Precious\MakeUp-app\backend
python manage.py makemigrations bookings
python manage.py migrate bookings
```

### 2. Update Main URLs

Add the bookings URLs to your main `config/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('api/v1/', include('apps.bookings.urls')),
]
```

### 3. Configure Celery (Optional but Recommended)

For automated notifications, create or update `config/celery.py`:

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('glamconnect')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'send-booking-reminders': {
        'task': 'apps.bookings.tasks.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    'auto-complete-past-bookings': {
        'task': 'apps.bookings.tasks.auto_complete_past_bookings',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-old-pending-bookings': {
        'task': 'apps.bookings.tasks.cleanup_old_pending_bookings',
        'schedule': crontab(hour=0, minute=0),  # Midnight daily
    },
}
```

Update `config/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 4. Start Celery Workers (Optional)

For background tasks to work:

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
celery -A config beat -l info
```

### 5. Create Superuser and Test

```bash
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://localhost:8000/admin/` to access the admin interface.

## Quick Test

### Via Django Shell

```python
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.profiles.models import MakeupArtistProfile, Availability
from apps.bookings.models import Service, Booking
from datetime import date, time, timedelta

User = get_user_model()

# Create test client
client = User.objects.create_user(
    email='client@test.com',
    password='test123',
    first_name='Test',
    last_name='Client',
    role='client'
)

# Create test artist
artist_user = User.objects.create_user(
    email='artist@test.com',
    password='test123',
    first_name='Test',
    last_name='Artist',
    role='artist'
)

artist_profile = MakeupArtistProfile.objects.create(
    user=artist_user,
    bio='Professional makeup artist',
    hourly_rate=100.00,
    location='New York'
)

# Create availability (Monday 9am-5pm)
Availability.objects.create(
    artist=artist_profile,
    day_of_week=0,
    start_time=time(9, 0),
    end_time=time(17, 0)
)

# Create service
service = Service.objects.create(
    artist=artist_profile,
    name='Bridal Makeup',
    description='Beautiful bridal makeup',
    price=150.00,
    duration_minutes=120,
    category='bridal'
)

# Create booking
tomorrow = date.today() + timedelta(days=1)
# Ensure it's a Monday
while tomorrow.weekday() != 0:
    tomorrow += timedelta(days=1)

booking = Booking.objects.create(
    client=client,
    artist=artist_profile,
    service=service,
    booking_date=tomorrow,
    start_time=time(10, 0),
    end_time=time(12, 0),
    location='123 Main St'
)

print(f"Created booking: {booking.booking_number}")
print(f"Status: {booking.status}")

# Accept booking
booking.accept()
print(f"Booking accepted at: {booking.accepted_at}")
```

### Via API

1. **Create a client and artist via admin or registration endpoint**

2. **Get JWT token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "client@test.com", "password": "test123"}'
```

3. **Create a booking:**
```bash
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "artist-uuid",
    "service": "service-uuid",
    "booking_date": "2026-03-17",
    "start_time": "10:00:00",
    "end_time": "12:00:00",
    "location": "123 Main St",
    "client_notes": "Please arrive early"
  }'
```

4. **Check availability:**
```bash
curl -X POST http://localhost:8000/api/v1/bookings/check_availability/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "artist-uuid",
    "booking_date": "2026-03-17",
    "start_time": "10:00:00",
    "end_time": "12:00:00"
  }'
```

## Environment Variables

Ensure these are set in your `.env` file:

```env
# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@glamconnect.com

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Troubleshooting

### Import Error: AbstractUser

If you get `ImportError: cannot import name 'AbstractUser' from 'django.contrib.auth.models.AbstractUser'`, fix in `apps/users/models.py`:

Change:
```python
from django.contrib.auth.models.AbstractUser import AbstractUser
```

To:
```python
from django.contrib.auth.models import AbstractUser
```

### Booking Date Constraint Error

If you get constraint errors about booking dates in the past, this is expected. The model enforces that bookings can only be made for future dates.

### Celery Not Running

If notifications aren't being sent, ensure:
1. Redis is running
2. Celery worker is running
3. Email settings are configured correctly

For development, you can use the console email backend:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Next Steps

1. Run migrations for notifications app:
   ```bash
   python manage.py makemigrations notifications
   python manage.py migrate notifications
   ```

2. Create test data via admin interface

3. Test the API endpoints using Postman or curl

4. Integrate with frontend applications

## Files Created

- `__init__.py` - App initialization
- `apps.py` - App configuration
- `models.py` - Service and Booking models
- `serializers.py` - DRF serializers
- `views.py` - API viewsets and actions
- `urls.py` - URL routing
- `permissions.py` - Custom permissions
- `admin.py` - Admin interface configuration
- `tasks.py` - Celery async tasks
- `utils.py` - Availability checking utilities
- `signals.py` - Django signals
- `filters.py` - Advanced filtering
- `tests.py` - Unit tests
- `README.md` - Documentation
- `SETUP.md` - This file
