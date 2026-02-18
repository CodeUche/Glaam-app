# Profiles API Reference

## Table of Contents
1. [Client Profiles](#client-profiles)
2. [Artist Profiles](#artist-profiles)
3. [Portfolio Images](#portfolio-images)
4. [Favorites](#favorites)
5. [Availability](#availability)
6. [Availability Exceptions](#availability-exceptions)

---

## Client Profiles

### List Client Profiles
**Staff only**
```http
GET /api/profiles/clients/
```

### Get Current Client Profile
```http
GET /api/profiles/clients/me/
```

**Response:**
```json
{
  "id": "uuid",
  "user": {
    "id": "uuid",
    "email": "client@example.com",
    "full_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+234..."
  },
  "profile_photo_url": "https://...",
  "bio": "Client bio",
  "preferred_location": "Lagos, Nigeria",
  "notification_preferences": {
    "email_notifications": true,
    "sms_notifications": false
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Update Client Profile
```http
PATCH /api/profiles/clients/me/
Content-Type: application/json

{
  "bio": "Updated bio",
  "preferred_location": "Abuja",
  "notification_preferences": {
    "email_notifications": true,
    "sms_notifications": true,
    "booking_updates": true
  }
}
```

---

## Artist Profiles

### List Artists (Cached - 5 minutes)
```http
GET /api/profiles/artists/
```

**Query Parameters:**
- `location` - Filter by location (partial match)
- `location_exact` - Filter by exact location
- `min_rating` - Minimum rating (0-5)
- `specialty` - Single specialty (bridal, editorial, glam, etc.)
- `specialties` - Multiple specialties (comma-separated)
- `min_price` - Minimum hourly rate
- `max_price` - Maximum hourly rate
- `price_range` - Predefined: budget (<50), moderate (50-100), premium (>100)
- `available` - true/false
- `verified` - true/false
- `min_experience` - Minimum years of experience
- `max_experience` - Maximum years of experience
- `experience_level` - beginner (<2), intermediate (2-5), expert (>5)
- `search` - Search across name, bio, location, specialties
- `ordering` - Sort by: rating, -rating, price, -price, experience, reviews, bookings, newest
- `page` - Page number
- `page_size` - Items per page

**Examples:**
```http
# Get bridal artists in Lagos with 4+ rating
GET /api/profiles/artists/?location=Lagos&specialty=bridal&min_rating=4.0

# Get premium verified artists ordered by rating
GET /api/profiles/artists/?price_range=premium&verified=true&ordering=-rating

# Search for specific artist
GET /api/profiles/artists/?search=beauty queen
```

**Response:**
```json
{
  "count": 100,
  "next": "http://.../api/profiles/artists/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "email": "artist@example.com",
        "full_name": "Jane Artist",
        "first_name": "Jane",
        "last_name": "Artist",
        "phone_number": "+234..."
      },
      "profile_photo_url": "https://...",
      "bio": "Professional makeup artist...",
      "specialties": ["bridal", "glam"],
      "years_of_experience": 5,
      "hourly_rate": "7500.00",
      "location": "Lagos, Nigeria",
      "is_available": true,
      "average_rating": "4.50",
      "total_reviews": 50,
      "total_bookings": 120,
      "verified": true,
      "featured_images": [
        {
          "id": "uuid",
          "image_url": "https://...",
          "category": "bridal"
        }
      ],
      "is_favorited": false,
      "total_favorites": 25
    }
  ]
}
```

### Get Artist Detail (Cached - 10 minutes)
```http
GET /api/profiles/artists/{id}/
```

**Response:**
```json
{
  "id": "uuid",
  "user": {...},
  "profile_photo_url": "https://...",
  "bio": "Detailed bio...",
  "specialties": ["bridal", "editorial", "glam"],
  "years_of_experience": 5,
  "hourly_rate": "7500.00",
  "location": "Lagos, Nigeria",
  "latitude": "6.5244",
  "longitude": "3.3792",
  "is_available": true,
  "average_rating": "4.50",
  "total_reviews": 50,
  "total_bookings": 120,
  "verified": true,
  "verification_date": "2024-01-01T00:00:00Z",
  "portfolio_images": [
    {
      "id": "uuid",
      "image_url_full": "https://...",
      "thumbnail_url_full": "https://...",
      "caption": "Beautiful bridal makeup",
      "category": "bridal",
      "display_order": 0,
      "is_featured": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "featured_images": [...],
  "is_favorited": true,
  "total_favorites": 25,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Get Current Artist Profile
**Artist only**
```http
GET /api/profiles/artists/me/
```

### Create Artist Profile
**Artist only**
```http
POST /api/profiles/artists/
Content-Type: application/json

{
  "bio": "Professional makeup artist with 5 years experience...",
  "specialties": ["bridal", "glam"],
  "years_of_experience": 5,
  "hourly_rate": 7500,
  "location": "Lagos, Nigeria",
  "latitude": 6.5244,
  "longitude": 3.3792,
  "is_available": true
}
```

### Update Artist Profile
**Artist only (own profile)**
```http
PATCH /api/profiles/artists/me/
Content-Type: application/json

{
  "hourly_rate": 8000,
  "is_available": false,
  "bio": "Updated bio..."
}
```

### Get Artist Portfolio
```http
GET /api/profiles/artists/{id}/portfolio/
```

**Query Parameters:**
- `category` - Filter by category

### Get Artist Availability
```http
GET /api/profiles/artists/{id}/availability/
```

### Toggle Favorite
**Authenticated users only**
```http
POST /api/profiles/artists/{id}/toggle_favorite/
```

**Response:**
```json
{
  "message": "Artist added to favorites.",
  "is_favorited": true
}
```

---

## Portfolio Images

### List Portfolio Images
```http
GET /api/profiles/portfolio/
```

**Query Parameters:**
- `artist` - Filter by artist ID
- `category` - Filter by category
- `is_featured` - Filter by featured status
- `ordering` - Sort by: order, -order, newest, -newest

### Get Own Portfolio
**Artist only**
```http
GET /api/profiles/portfolio/my_portfolio/
```

### Upload Portfolio Image
**Artist only**
```http
POST /api/profiles/portfolio/
Content-Type: multipart/form-data

{
  "image_url": <file>,
  "caption": "Beautiful bridal makeup",
  "category": "bridal",
  "display_order": 0,
  "is_featured": true
}
```

### Update Portfolio Image
**Artist only (own images)**
```http
PATCH /api/profiles/portfolio/{id}/
Content-Type: application/json

{
  "caption": "Updated caption",
  "is_featured": true
}
```

### Delete Portfolio Image
**Artist only (own images)**
```http
DELETE /api/profiles/portfolio/{id}/
```

### Toggle Featured Status
**Artist only (own images)**
```http
POST /api/profiles/portfolio/{id}/toggle_featured/
```

### Reorder Portfolio Images
**Artist only**
```http
POST /api/profiles/portfolio/reorder/
Content-Type: application/json

{
  "image_ids": ["uuid1", "uuid2", "uuid3"]
}
```

---

## Favorites

### List My Favorites
**Authenticated users only**
```http
GET /api/profiles/favorites/
GET /api/profiles/favorites/my_favorites/
```

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": "uuid",
      "artist": "artist_uuid",
      "artist_details": {
        "id": "uuid",
        "user": {...},
        "bio": "...",
        "average_rating": "4.50",
        ...
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Add Favorite
**Authenticated users only**
```http
POST /api/profiles/favorites/
Content-Type: application/json

{
  "artist": "artist_uuid"
}
```

### Remove Favorite
**Authenticated users only**
```http
DELETE /api/profiles/favorites/{id}/
```

---

## Availability

### List Availability
```http
GET /api/profiles/availability/
```

**Query Parameters:**
- `artist` - Filter by artist ID

### Get My Schedule
**Artist only**
```http
GET /api/profiles/availability/my_schedule/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "artist": "artist_uuid",
    "day_of_week": 1,
    "day_name": "Tuesday",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Availability
**Artist only**
```http
POST /api/profiles/availability/
Content-Type: application/json

{
  "day_of_week": 1,
  "start_time": "09:00",
  "end_time": "17:00",
  "is_active": true
}
```

**Validation:**
- `day_of_week`: 0-6 (Monday-Sunday)
- `start_time`: Must be before `end_time`
- No overlapping time slots for the same day

### Update Availability
**Artist only (own schedule)**
```http
PATCH /api/profiles/availability/{id}/
Content-Type: application/json

{
  "start_time": "10:00",
  "end_time": "18:00"
}
```

### Delete Availability
**Artist only (own schedule)**
```http
DELETE /api/profiles/availability/{id}/
```

---

## Availability Exceptions

### List Availability Exceptions
```http
GET /api/profiles/availability-exceptions/
```

**Query Parameters:**
- `artist` - Filter by artist ID
- `show_past` - Include past exceptions (default: false)

### Get My Exceptions
**Artist only**
```http
GET /api/profiles/availability-exceptions/my_exceptions/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "artist": "artist_uuid",
    "date": "2024-12-25",
    "is_available": false,
    "start_time": null,
    "end_time": null,
    "reason": "Christmas Holiday",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Exception
**Artist only**
```http
POST /api/profiles/availability-exceptions/
Content-Type: application/json

{
  "date": "2024-12-25",
  "is_available": false,
  "reason": "Christmas Holiday"
}
```

**Or for special availability:**
```json
{
  "date": "2024-12-31",
  "is_available": true,
  "start_time": "18:00",
  "end_time": "23:00",
  "reason": "New Year's Eve special hours"
}
```

**Validation:**
- `date`: Cannot be in the past
- If `is_available` is true, `start_time` and `end_time` are required

### Update Exception
**Artist only (own exceptions)**
```http
PATCH /api/profiles/availability-exceptions/{id}/
Content-Type: application/json

{
  "reason": "Updated reason"
}
```

### Delete Exception
**Artist only (own exceptions)**
```http
DELETE /api/profiles/availability-exceptions/{id}/
```

---

## Common Response Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no response body (DELETE)
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded (if configured)
- `500 Internal Server Error` - Server error

## Error Response Format

```json
{
  "detail": "Error message",
  "field_name": ["Field-specific error message"]
}
```

## Rate Limiting

To enable rate limiting, add to `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## Pagination

Default pagination: 20 items per page

Customize with query parameters:
- `page` - Page number
- `page_size` - Items per page (max: 100)

## Authentication

All authenticated endpoints require JWT token:

```http
Authorization: Bearer <access_token>
```

To obtain token:
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

## Cache Headers

Cached endpoints return these headers:
- `Cache-Control: max-age=300` (for list views)
- `Cache-Control: max-age=600` (for detail views)

To bypass cache (admin only):
```http
GET /api/profiles/artists/?no_cache=1
```
