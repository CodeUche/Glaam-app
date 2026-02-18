# Bookings App - Quick Start Guide

## 1. Run Migrations (First Time Setup)

```bash
cd c:\Users\Precious\MakeUp-app\backend
python manage.py makemigrations bookings
python manage.py makemigrations notifications
python manage.py migrate
```

## 2. Create Test Data

### Via Django Shell

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.profiles.models import MakeupArtistProfile, Availability
from apps.bookings.models import Service, Booking
from datetime import date, time, timedelta

User = get_user_model()

# Create artist
artist_user = User.objects.create_user(
    email='artist@test.com',
    password='test123',
    first_name='Jane',
    last_name='Doe',
    role='artist'
)

artist = MakeupArtistProfile.objects.create(
    user=artist_user,
    bio='Professional makeup artist',
    hourly_rate=100.00,
    location='New York',
    specialties=['bridal', 'glam']
)

# Add availability (Monday-Friday, 9am-5pm)
for day in range(5):
    Availability.objects.create(
        artist=artist,
        day_of_week=day,
        start_time=time(9, 0),
        end_time=time(17, 0)
    )

# Create services
Service.objects.create(
    artist=artist,
    name='Bridal Makeup',
    description='Complete bridal makeup package',
    price=200.00,
    duration_minutes=120,
    category='bridal'
)

Service.objects.create(
    artist=artist,
    name='Natural Makeup',
    description='Natural everyday look',
    price=80.00,
    duration_minutes=60,
    category='natural'
)

# Create client
client = User.objects.create_user(
    email='client@test.com',
    password='test123',
    first_name='John',
    last_name='Smith',
    role='client'
)

print("✓ Test data created successfully!")
print(f"Artist: {artist_user.email} (password: test123)")
print(f"Client: {client.email} (password: test123)")
```

## 3. Test API Endpoints

### Get JWT Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "client@test.com", "password": "test123"}'
```

Save the `access` token from the response.

### List Services

```bash
curl -X GET http://localhost:8000/api/v1/bookings/services/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Create Booking

```bash
curl -X POST http://localhost:8000/api/v1/bookings/bookings/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "ARTIST_UUID",
    "service": "SERVICE_UUID",
    "booking_date": "2026-03-17",
    "start_time": "10:00:00",
    "end_time": "12:00:00",
    "location": "123 Main St, NYC"
  }'
```

### Check Availability

```bash
curl -X POST http://localhost:8000/api/v1/bookings/bookings/check_availability/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "ARTIST_UUID",
    "booking_date": "2026-03-17",
    "start_time": "10:00:00",
    "end_time": "12:00:00"
  }'
```

## 4. Admin Interface

1. Create superuser:
```bash
python manage.py createsuperuser
```

2. Run server:
```bash
python manage.py runserver
```

3. Visit: http://localhost:8000/admin/

4. Navigate to:
   - Bookings → Services
   - Bookings → Bookings

## 5. Start Celery (Optional)

### Terminal 1: Redis
```bash
redis-server
```

### Terminal 2: Celery Worker
```bash
cd c:\Users\Precious\MakeUp-app\backend
celery -A config worker -l info
```

### Terminal 3: Celery Beat (Scheduled Tasks)
```bash
cd c:\Users\Precious\MakeUp-app\backend
celery -A config beat -l info
```

## 6. Common Operations

### Accept a Booking (as Artist)

```python
# In Django shell
from apps.bookings.models import Booking

booking = Booking.objects.get(booking_number='BK...')
booking.accept()
```

### Complete a Booking

```python
booking.complete()
```

### Cancel a Booking

```python
booking.cancel(cancelled_by='client', reason='Change of plans')
```

### Check Availability

```python
from apps.bookings.utils import check_artist_availability
from apps.profiles.models import MakeupArtistProfile
from datetime import date, time

artist = MakeupArtistProfile.objects.first()
is_available = check_artist_availability(
    artist=artist,
    booking_date=date(2026, 3, 17),
    start_time=time(10, 0),
    end_time=time(12, 0)
)
print(f"Available: {is_available}")
```

## 7. Troubleshooting

### "Artist not found" Error
Ensure the artist has a MakeupArtistProfile created.

### "Not available" Error
Check:
1. Artist has Availability records for the day of week
2. Time falls within availability window
3. No conflicting bookings exist
4. Artist `is_available=True`

### Email not sending
Check `.env` file has correct email settings, or use console backend for testing:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Migration errors
Delete existing migrations and recreate:
```bash
rm backend/apps/bookings/migrations/0*.py
python manage.py makemigrations bookings
python manage.py migrate
```

## 8. Environment Setup

Create `.env` file in backend directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/glamconnect

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@glamconnect.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## 9. Run Tests

```bash
python manage.py test apps.bookings
```

## 10. Next Steps

- Create more test data
- Test all API endpoints
- Set up frontend integration
- Configure production email settings
- Set up monitoring and logging

## Quick Reference

**App Location:** `c:\Users\Precious\MakeUp-app\backend\apps\bookings\`

**Documentation:**
- README.md - Complete feature docs
- API_DOCUMENTATION.md - Full API reference
- SETUP.md - Detailed setup guide

**Key Models:**
- Service - Artist services
- Booking - Client bookings

**Key Views:**
- ServiceViewSet - Service CRUD
- BookingViewSet - Booking management

**Key Utils:**
- check_artist_availability() - Availability validation
- get_available_time_slots() - Time slot generation

**Celery Tasks:**
- send_booking_notification() - Notifications
- send_booking_reminders() - Daily reminders
- auto_complete_past_bookings() - Auto-completion
