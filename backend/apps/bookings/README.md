# Bookings App

The bookings app handles all booking-related functionality for GlamConnect, including:

- Service management for makeup artists
- Booking creation by clients
- Booking status management (pending, accepted, rejected, completed, cancelled)
- Artist availability checking
- Double-booking prevention
- Automated notifications via Celery tasks

## Models

### Service
Represents services offered by makeup artists.

**Fields:**
- `artist` (ForeignKey): The makeup artist offering the service
- `name` (CharField): Service name
- `description` (TextField): Service description
- `price` (DecimalField): Service price
- `duration_minutes` (PositiveIntegerField): Service duration in minutes
- `category` (CharField): Service category
- `is_active` (BooleanField): Whether the service is active

### Booking
Represents a booking between a client and an artist.

**Fields:**
- `booking_number` (CharField): Unique booking identifier
- `client` (ForeignKey): The client making the booking
- `artist` (ForeignKey): The artist being booked
- `service` (ForeignKey): The service being booked
- `booking_date` (DateField): Date of the booking
- `start_time` (TimeField): Start time
- `end_time` (TimeField): End time
- `status` (CharField): Booking status (pending, accepted, rejected, completed, cancelled)
- `location` (CharField): Booking location
- `client_notes` (TextField): Notes from the client
- `artist_notes` (TextField): Notes from the artist
- `cancellation_reason` (TextField): Reason for cancellation
- `cancelled_by` (CharField): Who cancelled (client/artist)
- `total_price` (DecimalField): Total price
- Timestamps: `created_at`, `updated_at`, `accepted_at`, `completed_at`, `cancelled_at`

## API Endpoints

### Services

**List Services**
```
GET /api/v1/bookings/services/
```
Query params: `artist`, `category`, `is_active`, `search`, `ordering`

**Create Service** (Artists only)
```
POST /api/v1/bookings/services/
```
Body:
```json
{
  "name": "Bridal Makeup",
  "description": "Beautiful bridal makeup for your special day",
  "price": 150.00,
  "duration_minutes": 120,
  "category": "bridal"
}
```

**Update Service** (Owner only)
```
PATCH /api/v1/bookings/services/{id}/
```

**Delete Service** (Owner only - soft delete)
```
DELETE /api/v1/bookings/services/{id}/
```

### Bookings

**List Bookings**
```
GET /api/v1/bookings/bookings/
```
- Clients see their own bookings
- Artists see bookings for them
- Query params: `status`, `booking_date`, `artist`, `service`, `search`, `ordering`

**Create Booking** (Clients only)
```
POST /api/v1/bookings/bookings/
```
Body:
```json
{
  "artist": "uuid",
  "service": "uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "location": "123 Main St, City",
  "client_notes": "Please bring extra makeup"
}
```

**Get Booking Detail**
```
GET /api/v1/bookings/bookings/{id}/
```

**Accept Booking** (Artists only)
```
POST /api/v1/bookings/bookings/{id}/accept/
```
Body (optional):
```json
{
  "reason": "Optional note"
}
```

**Reject Booking** (Artists only)
```
POST /api/v1/bookings/bookings/{id}/reject/
```
Body (optional):
```json
{
  "reason": "Not available at this time"
}
```

**Complete Booking** (Artists only)
```
POST /api/v1/bookings/bookings/{id}/complete/
```

**Cancel Booking** (Client or Artist)
```
POST /api/v1/bookings/bookings/{id}/cancel/
```
Body (optional):
```json
{
  "reason": "Change of plans"
}
```

**Check Availability**
```
POST /api/v1/bookings/bookings/check_availability/
```
Body:
```json
{
  "artist_id": "uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00"
}
```

**Get Available Slots**
```
GET /api/v1/bookings/bookings/available_slots/?artist_id=uuid&booking_date=2026-03-15&duration_minutes=120
```

**Get Statistics**
```
GET /api/v1/bookings/bookings/statistics/
```
Returns booking statistics for the current user (client or artist).

## Permissions

- **IsClient**: User must be a client
- **IsArtist**: User must be an artist
- **IsBookingClient**: User must be the client of the booking
- **IsBookingArtist**: User must be the artist of the booking
- **IsBookingParticipant**: User must be either the client or artist
- **IsServiceOwner**: User must be the owner of the service

## Availability Checking

The `check_artist_availability()` utility function validates:

1. Artist is generally available (`is_available=True`)
2. Artist has regular availability for the day of week
3. Requested time fits within availability windows
4. No availability exceptions block the date
5. No conflicting bookings exist

### Double-booking Prevention

The system prevents double-booking by:
1. Checking for overlapping bookings in the same date/time
2. Only considering bookings with status `pending` or `accepted`
3. Using database-level validation
4. Validating on creation and updates

## Celery Tasks

### Automated Tasks

**`send_booking_notification`**
- Sends email and in-app notification for booking events
- Triggered on: creation, acceptance, rejection, completion, cancellation
- Retries up to 3 times on failure

**`send_booking_reminders`**
- Sends reminders 24 hours before accepted bookings
- Run daily via Celery Beat

**`auto_complete_past_bookings`**
- Automatically marks accepted bookings as completed after the date passes
- Run hourly via Celery Beat

**`cleanup_old_pending_bookings`**
- Cancels pending bookings past their booking date
- Run daily via Celery Beat

### Celery Beat Schedule

Add to your `celery.py`:

```python
from celery.schedules import crontab

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

## Usage Examples

### Creating a Booking (Client)

```python
from apps.bookings.models import Booking, Service
from apps.profiles.models import MakeupArtistProfile
from datetime import date, time

# Get artist and service
artist = MakeupArtistProfile.objects.get(id='...')
service = Service.objects.get(id='...')

# Create booking
booking = Booking.objects.create(
    client=request.user,
    artist=artist,
    service=service,
    booking_date=date(2026, 3, 15),
    start_time=time(10, 0),
    end_time=time(12, 0),
    location='123 Main St',
    client_notes='Please arrive 10 minutes early'
)
```

### Accepting a Booking (Artist)

```python
booking = Booking.objects.get(id='...')
booking.accept()
```

### Checking Availability

```python
from apps.bookings.utils import check_artist_availability
from datetime import date, time

is_available = check_artist_availability(
    artist=artist,
    booking_date=date(2026, 3, 15),
    start_time=time(10, 0),
    end_time=time(12, 0)
)
```

## Testing

Run tests:
```bash
python manage.py test apps.bookings
```

## Dependencies

- Django REST Framework
- django-filter
- Celery
- Redis (for Celery broker)

## Migration

To create and run migrations:

```bash
python manage.py makemigrations bookings
python manage.py migrate bookings
```

## Admin Interface

The bookings app includes a comprehensive admin interface with:
- Service management
- Booking management with colored status badges
- Bulk actions (mark as completed, cancel)
- Advanced filtering and searching
- Optimized queries with select_related
