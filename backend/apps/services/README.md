# Services App

The Services app manages makeup artist service offerings in the GlamConnect platform.

## Overview

This app allows makeup artists to create, manage, and showcase their service offerings. Clients can browse and view available services before making bookings.

## Features

- Service CRUD operations (Create, Read, Update, Delete)
- Artist-only service management
- Service categorization (Bridal, Editorial, Natural, Glam, SFX, etc.)
- Pricing and duration management
- Active/inactive status control
- Booking count tracking
- Search and filtering capabilities
- Popular services ranking

## Models

### Service

Main model representing makeup artist services.

**Fields:**
- `id` (UUID): Primary key
- `artist` (FK): Link to MakeupArtistProfile
- `name` (CharField): Service name
- `description` (TextField): Detailed service description
- `category` (CharField): Service category (choices from ServiceCategory)
- `price` (DecimalField): Service price
- `duration` (PositiveIntegerField): Duration in minutes (15-480)
- `is_active` (BooleanField): Availability status
- `booking_count` (PositiveIntegerField): Total bookings count
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp

**Properties:**
- `duration_hours`: Returns duration in hours (decimal)
- `is_available`: Checks if service is active and artist is available

**Methods:**
- `increment_booking_count()`: Increments booking count

## Serializers

### ServiceSerializer
Complete serializer for service details including read-only artist information.

### ServiceListSerializer
Lightweight serializer optimized for list views.

### ServiceCreateUpdateSerializer
Serializer for creating and updating services (excludes artist field).

## API Endpoints

### Base URL: `/api/services/`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/` | Any | List all active services |
| GET | `/{id}/` | Any | Retrieve service details |
| POST | `/` | Artist only | Create new service |
| PUT/PATCH | `/{id}/` | Owner only | Update service |
| DELETE | `/{id}/` | Owner only | Delete service |
| GET | `/my_services/` | Artist only | Get current artist's services |
| POST | `/{id}/toggle_active/` | Owner only | Toggle service active status |
| GET | `/categories/` | Any | Get service categories |
| GET | `/popular/` | Any | Get top 10 popular services |
| GET | `/{artist_id}/by_artist/` | Any | Get services by artist |

## Query Parameters

### Filtering
- `category`: Filter by service category
- `is_active`: Filter by active status
- `artist`: Filter by artist ID
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `min_duration`: Minimum duration (minutes)
- `max_duration`: Maximum duration (minutes)

### Searching
- `search`: Search in name, description, and artist names

### Ordering
- `ordering`: Sort by `price`, `duration`, `booking_count`, or `created_at`
- Use `-` prefix for descending order (e.g., `-price`)

## Permissions

### IsArtistOwnerOrReadOnly
- Read access: All authenticated users
- Write access: Artist who owns the service

### IsArtistOwner
- All access: Artist who owns the service only

## Service Categories

1. **Bridal** (`bridal`) - Bridal makeup services
2. **Editorial** (`editorial`) - Editorial and photoshoot makeup
3. **Natural** (`natural`) - Natural/everyday makeup
4. **Glam** (`glam`) - Glamour makeup
5. **SFX** (`sfx`) - Special effects makeup
6. **Airbrush** (`airbrush`) - Airbrush makeup
7. **Theatrical** (`theatrical`) - Theatrical makeup
8. **Consultation** (`consultation`) - Makeup consultation
9. **Other** (`other`) - Other services

## Usage Examples

### Create a Service (Artist)
```python
POST /api/services/
{
    "name": "Bridal Makeup Package",
    "description": "Complete bridal makeup with trial session",
    "category": "bridal",
    "price": "250.00",
    "duration": 120
}
```

### Update Service
```python
PATCH /api/services/{id}/
{
    "price": "275.00",
    "is_active": true
}
```

### List Services with Filters
```python
GET /api/services/?category=bridal&min_price=100&max_price=500&ordering=-booking_count
```

### Toggle Service Status
```python
POST /api/services/{id}/toggle_active/
```

## Admin Interface

The admin interface provides:
- Service listing with filtering and search
- Formatted price and duration display
- Artist profile links
- Active status indicators
- Bulk activate/deactivate actions
- Read-only fields for metrics and timestamps

## Testing

Run tests with:
```bash
python manage.py test apps.services
```

Tests cover:
- Model creation and validation
- API endpoint access control
- Permission verification
- CRUD operations
- Custom actions

## Database Indexes

Optimized indexes for:
- Artist and active status queries
- Category filtering
- Popular services (booking count)
- Combined artist-category lookups

## Constraints

- Price must be non-negative
- Duration must be between 15 and 480 minutes (15 min to 8 hours)
- Services must be linked to a valid artist profile

## Signals

Post-save and post-delete signals are available for:
- Logging service changes
- Triggering notifications
- Analytics tracking

## Integration

This app integrates with:
- **profiles**: Links to MakeupArtistProfile
- **bookings**: Services can be booked by clients
- **users**: Uses user authentication and permissions
