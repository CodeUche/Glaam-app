# Services App - Quick Start Guide

Get started with the GlamConnect Services app in 5 minutes!

## Prerequisites

- Django project set up and running
- `apps.users` app installed and migrated
- `apps.profiles` app installed and migrated
- At least one artist user with an artist profile

## Quick Setup (5 Steps)

### 1. Add to INSTALLED_APPS

```python
# backend/config/settings.py
INSTALLED_APPS = [
    # ... existing apps
    'apps.services',
]
```

### 2. Include URLs

```python
# backend/config/urls.py
urlpatterns = [
    # ... existing URLs
    path('api/services/', include('apps.services.urls')),
]
```

### 3. Run Migrations

```bash
python manage.py makemigrations services
python manage.py migrate services
```

### 4. Create Sample Data (Optional)

```bash
# Create sample services for the first artist in database
python manage.py create_sample_services

# Or for a specific artist
python manage.py create_sample_services --artist-email artist@example.com

# Clear existing services first
python manage.py create_sample_services --clear
```

### 5. Test the API

Start the server:
```bash
python manage.py runserver
```

Visit:
- http://localhost:8000/api/services/ (List services)
- http://localhost:8000/api/services/categories/ (Get categories)

## Quick API Reference

### Authentication Required Endpoints

**Create Service** (Artist only)
```bash
POST /api/services/
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
    "name": "Evening Glam Makeup",
    "description": "Full glam look for evening events",
    "category": "glam",
    "price": "150.00",
    "duration": 90
}
```

**Update Service** (Owner only)
```bash
PATCH /api/services/{service_id}/
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
    "price": "175.00",
    "is_active": true
}
```

**My Services** (Artist only)
```bash
GET /api/services/my_services/
Authorization: Bearer {your_access_token}
```

**Toggle Service Active** (Owner only)
```bash
POST /api/services/{service_id}/toggle_active/
Authorization: Bearer {your_access_token}
```

### Public Endpoints

**List All Services**
```bash
GET /api/services/
```

**Filter Services**
```bash
# By category
GET /api/services/?category=bridal

# By price range
GET /api/services/?min_price=100&max_price=300

# By duration
GET /api/services/?min_duration=60&max_duration=120

# Search
GET /api/services/?search=bridal

# Sort by price (descending)
GET /api/services/?ordering=-price
```

**Get Service Details**
```bash
GET /api/services/{service_id}/
```

**Get Categories**
```bash
GET /api/services/categories/
```

**Get Popular Services**
```bash
GET /api/services/popular/
```

## Available Service Categories

- `bridal` - Bridal Makeup
- `editorial` - Editorial Makeup
- `natural` - Natural/Everyday Makeup
- `glam` - Glamour Makeup
- `sfx` - Special Effects Makeup
- `airbrush` - Airbrush Makeup
- `theatrical` - Theatrical Makeup
- `consultation` - Consultation
- `other` - Other

## Service Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Service name (max 200 chars) |
| description | text | Yes | Detailed description |
| category | string | Yes | One of the categories above |
| price | decimal | Yes | Price (0 - 999,999.99) |
| duration | integer | Yes | Duration in minutes (15-480) |
| is_active | boolean | No | Active status (default: true) |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Service unique identifier |
| artist | UUID | Artist profile ID |
| artist_name | string | Artist full name |
| name | string | Service name |
| description | text | Service description |
| category | string | Category code |
| category_display | string | Human-readable category |
| price | decimal | Service price |
| duration | integer | Duration in minutes |
| duration_hours | decimal | Duration in hours |
| is_active | boolean | Active status |
| is_available | boolean | Available for booking |
| booking_count | integer | Total bookings |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

## Common Workflows

### Artist Creating Services

1. Login as artist to get access token
2. Create services via POST /api/services/
3. View created services via GET /api/services/my_services/
4. Update services as needed via PATCH /api/services/{id}/
5. Toggle active status via POST /api/services/{id}/toggle_active/

### Client Browsing Services

1. Browse all services via GET /api/services/
2. Filter by category, price, or duration
3. Search for specific services
4. View service details via GET /api/services/{id}/
5. Proceed to booking (requires bookings app)

## Django Admin

Access the admin interface at:
```
http://localhost:8000/admin/services/service/
```

Features:
- View all services
- Filter by category, active status, date
- Search by name, description, artist
- Bulk activate/deactivate services
- View formatted prices and durations

## Testing

Run the test suite:
```bash
# All tests
python manage.py test apps.services

# Specific test class
python manage.py test apps.services.tests.ServiceModelTests
python manage.py test apps.services.tests.ServiceAPITests

# With coverage
coverage run --source='apps.services' manage.py test apps.services
coverage report
```

## Troubleshooting

### "Only makeup artists can create services"
- Ensure user.role == 'artist'
- Ensure user has an associated MakeupArtistProfile

### "Permission denied" errors
- Check if user is authenticated
- Verify user owns the service they're trying to modify
- Confirm proper Authorization header format

### Services not appearing in list
- Check if services are marked as is_active=True
- Verify artist profile is_available=True
- Check if filters are excluding results

## Next Steps

1. Integrate with bookings app for service booking
2. Add service images/photos
3. Implement service reviews and ratings
4. Add service packages (multiple services bundled)
5. Implement service availability calendar

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review the INTEGRATION.md for setup help
3. Check the test files for usage examples
4. Review the inline code documentation

## File Structure

```
services/
├── __init__.py              # App initialization
├── admin.py                 # Django admin configuration
├── apps.py                  # App configuration
├── models.py                # Service model
├── serializers.py           # DRF serializers
├── views.py                 # API views
├── urls.py                  # URL routing
├── permissions.py           # Custom permissions
├── signals.py               # Django signals
├── tests.py                 # Test suite
├── README.md                # Full documentation
├── INTEGRATION.md           # Integration guide
├── QUICKSTART.md            # This file
├── fixtures/
│   └── sample_services.json # Sample data
└── management/
    └── commands/
        └── create_sample_services.py  # Management command
```
