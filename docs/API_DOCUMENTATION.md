# GlamConnect API Documentation

**Base URL:** `https://api.glamconnect.com/api/v1/`

**Authentication:** JWT Bearer Token
```
Authorization: Bearer <access_token>
```

---

## Authentication

### Register
```
POST /auth/register/
```
**Body:**
```json
{
  "email": "jane@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "client"  // "client" or "artist"
}
```
**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "client",
    "is_verified": false
  },
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

### Login
```
POST /auth/login/
```
**Body:**
```json
{
  "email": "jane@example.com",
  "password": "SecurePass123!"
}
```
**Response:** `200 OK` — Same format as register.

### Logout
```
POST /auth/logout/
Authorization: Bearer <token>
```
**Body:**
```json
{
  "refresh": "eyJ..."
}
```

### Refresh Token
```
POST /auth/refresh/
```
**Body:**
```json
{
  "refresh": "eyJ..."
}
```
**Response:**
```json
{
  "access": "eyJ..."
}
```

### Get Current User
```
GET /auth/me/
Authorization: Bearer <token>
```

### Change Password
```
POST /auth/password/change/
Authorization: Bearer <token>
```
**Body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!",
  "new_password_confirm": "NewPass456!"
}
```

### Request Password Reset
```
POST /auth/password/reset/
```
**Body:**
```json
{
  "email": "jane@example.com"
}
```

### Confirm Password Reset
```
POST /auth/password/reset/confirm/
```
**Body:**
```json
{
  "token": "reset-token-here",
  "new_password": "NewPass456!",
  "new_password_confirm": "NewPass456!"
}
```

---

## Artists (Profiles)

### List Artists (with Search & Filters)
```
GET /artists/artists/
```
**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Search by name, bio, location |
| `location` | string | Filter by location |
| `specialties` | string | Filter by specialty (bridal, editorial, natural, glam, sfx) |
| `min_rating` | decimal | Minimum average rating |
| `min_price` | decimal | Minimum hourly rate |
| `max_price` | decimal | Maximum hourly rate |
| `is_available` | boolean | Only available artists |
| `ordering` | string | Order by: rating, price, -rating, -price, created_at |

**Response:** `200 OK` — Paginated list of artist profiles.

### Get Artist Detail
```
GET /artists/artists/{id}/
```
**Response:** Full artist profile with portfolio images, services, and reviews.

### Update Artist Profile (Owner Only)
```
PATCH /artists/artists/{id}/
Authorization: Bearer <artist_token>
```
**Body:**
```json
{
  "bio": "Updated bio...",
  "hourly_rate": 85.00,
  "specialties": ["bridal", "glam"],
  "is_available": true
}
```

### Portfolio Images
```
GET    /artists/portfolio/                  # List portfolio images
POST   /artists/portfolio/                  # Upload image (artist only)
DELETE /artists/portfolio/{id}/             # Delete image (owner only)
```
**Upload Body (multipart/form-data):**
- `image_url`: File
- `caption`: string
- `category`: string (bridal, editorial, natural, etc.)

### Favorites
```
GET    /artists/favorites/                  # List client's favorites
POST   /artists/favorites/                  # Add to favorites
DELETE /artists/favorites/{id}/             # Remove from favorites
```
**Add Favorite Body:**
```json
{
  "artist": "artist-profile-uuid"
}
```

### Availability
```
GET    /artists/availability/               # List artist's availability
POST   /artists/availability/               # Set availability (artist only)
PATCH  /artists/availability/{id}/          # Update availability
DELETE /artists/availability/{id}/          # Remove availability
```
**Body:**
```json
{
  "day_of_week": 1,
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "is_active": true
}
```

---

## Services

### List Services
```
GET /services/
```
**Query Parameters:** `artist`, `category`, `is_active`, `min_price`, `max_price`

### Create Service (Artist Only)
```
POST /services/
Authorization: Bearer <artist_token>
```
**Body:**
```json
{
  "name": "Bridal Makeup Package",
  "description": "Full bridal makeup with trial session.",
  "category": "bridal",
  "price": 250.00,
  "duration": 120
}
```

### Update / Delete Service
```
PATCH  /services/{id}/     # Update (owner only)
DELETE /services/{id}/     # Delete (owner only)
```

---

## Bookings

### List Bookings
```
GET /bookings/bookings/
Authorization: Bearer <token>
```
Returns bookings for the current user (filtered by role).

**Query Parameters:** `status`, `booking_date`, `date_from`, `date_to`

### Create Booking (Client Only)
```
POST /bookings/bookings/
Authorization: Bearer <client_token>
```
**Body:**
```json
{
  "artist": "artist-profile-uuid",
  "service": "service-uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "location": "123 Main St, New York",
  "client_notes": "Bridal trial - please bring samples"
}
```
**Response:** `201 Created`
```json
{
  "id": "uuid",
  "booking_number": "GC-20260315-ABC123",
  "status": "pending",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "total_price": 250.00,
  ...
}
```

### Get Booking Detail
```
GET /bookings/bookings/{id}/
```

### Accept Booking (Artist Only)
```
POST /bookings/bookings/{id}/accept/
Authorization: Bearer <artist_token>
```

### Reject Booking (Artist Only)
```
POST /bookings/bookings/{id}/reject/
Authorization: Bearer <artist_token>
```
**Body:**
```json
{
  "reason": "Not available on this date"
}
```

### Complete Booking (Artist Only)
```
POST /bookings/bookings/{id}/complete/
Authorization: Bearer <artist_token>
```

### Cancel Booking
```
POST /bookings/bookings/{id}/cancel/
Authorization: Bearer <token>
```
**Body:**
```json
{
  "reason": "Change of plans"
}
```

### Check Availability
```
POST /bookings/bookings/check_availability/
```
**Body:**
```json
{
  "artist": "artist-profile-uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00"
}
```

---

## Reviews

### List Reviews
```
GET /reviews/
```
**Query Parameters:** `artist`, `client`, `min_rating`, `max_rating`, `ordering`

### Create Review (Client Only, Completed Booking Required)
```
POST /reviews/
Authorization: Bearer <client_token>
```
**Body:**
```json
{
  "booking": "booking-uuid",
  "rating": 5,
  "comment": "Absolutely amazing work! The bridal look was perfect."
}
```

### Artist Response
```
PATCH /reviews/{id}/respond/
Authorization: Bearer <artist_token>
```
**Body:**
```json
{
  "artist_response": "Thank you so much! It was a pleasure working with you."
}
```

### Review Statistics
```
GET /reviews/stats/?artist=<artist-uuid>
```
**Response:**
```json
{
  "total_reviews": 42,
  "average_rating": 4.7,
  "rating_distribution": {
    "5": 25, "4": 10, "3": 5, "2": 1, "1": 1
  }
}
```

---

## Notifications

### List Notifications
```
GET /notifications/
Authorization: Bearer <token>
```

### Mark as Read
```
PATCH /notifications/{id}/read/
```

### Mark All as Read
```
PATCH /notifications/read-all/
```

---

## WebSocket Events

### Connection
```
ws://api.glamconnect.com/ws/notifications/?token=<jwt_access_token>
```

### Event Types

**Incoming (Server → Client):**
- `booking.created` — New booking request
- `booking.accepted` — Booking accepted
- `booking.rejected` — Booking rejected
- `booking.completed` — Booking marked complete
- `booking.cancelled` — Booking cancelled
- `booking.reminder` — Upcoming booking reminder
- `review.received` — New review received
- `artist.status` — Artist availability change
- `notification.new` — General notification
- `notification.unread_count` — Updated unread count

**Outgoing (Client → Server):**
- `ping` — Keep alive
- `mark_read` — Mark notification as read
- `get_unread_count` — Request unread count

---

## Error Response Format

All errors follow this format:
```json
{
  "success": false,
  "error": {
    "message": "Human-readable error message",
    "details": {
      "field_name": ["Error details"]
    }
  }
}
```

## Rate Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Authentication | 5 requests/minute |
| General API | 1000 requests/hour |
| Anonymous | 100 requests/hour |
| File Upload | 10 requests/minute |

## Pagination

Responses use cursor-based pagination:
```json
{
  "next": "https://api.glamconnect.com/api/v1/artists/?cursor=abc123",
  "previous": null,
  "results": [...]
}
```
