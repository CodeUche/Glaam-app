# Bookings API Documentation

## Base URL
```
http://localhost:8000/api/v1/
```

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Services Endpoints

### 1. List Services

**Endpoint:** `GET /bookings/services/`

**Description:** List all active services. Artists see their own services (including inactive).

**Query Parameters:**
- `artist` (UUID): Filter by artist ID
- `category` (string): Filter by category
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name, description, category
- `ordering` (string): Order by fields (price, duration_minutes, created_at)
- `page` (int): Page number for pagination

**Response:** `200 OK`
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/v1/bookings/services/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "artist": "artist-uuid",
      "artist_name": "Jane Doe",
      "artist_id": "artist-uuid",
      "name": "Bridal Makeup",
      "description": "Beautiful bridal makeup for your special day",
      "price": "150.00",
      "duration_minutes": 120,
      "category": "bridal",
      "is_active": true,
      "created_at": "2026-02-17T10:00:00Z",
      "updated_at": "2026-02-17T10:00:00Z"
    }
  ]
}
```

### 2. Create Service (Artists Only)

**Endpoint:** `POST /bookings/services/`

**Permissions:** Artist role required

**Request Body:**
```json
{
  "name": "Bridal Makeup",
  "description": "Beautiful bridal makeup for your special day",
  "price": 150.00,
  "duration_minutes": 120,
  "category": "bridal"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "artist": "artist-uuid",
  "artist_name": "Jane Doe",
  "artist_id": "artist-uuid",
  "name": "Bridal Makeup",
  "description": "Beautiful bridal makeup for your special day",
  "price": "150.00",
  "duration_minutes": 120,
  "category": "bridal",
  "is_active": true,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

### 3. Get Service Detail

**Endpoint:** `GET /bookings/services/{id}/`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "artist": "artist-uuid",
  "artist_name": "Jane Doe",
  "artist_id": "artist-uuid",
  "name": "Bridal Makeup",
  "description": "Beautiful bridal makeup for your special day",
  "price": "150.00",
  "duration_minutes": 120,
  "category": "bridal",
  "is_active": true,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

### 4. Update Service (Owner Only)

**Endpoint:** `PATCH /bookings/services/{id}/`

**Permissions:** Must be the service owner (artist)

**Request Body:** (All fields optional)
```json
{
  "name": "Premium Bridal Makeup",
  "price": 200.00,
  "is_active": false
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "artist": "artist-uuid",
  "artist_name": "Jane Doe",
  "artist_id": "artist-uuid",
  "name": "Premium Bridal Makeup",
  "description": "Beautiful bridal makeup for your special day",
  "price": "200.00",
  "duration_minutes": 120,
  "category": "bridal",
  "is_active": false,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T11:00:00Z"
}
```

### 5. Delete Service (Soft Delete)

**Endpoint:** `DELETE /bookings/services/{id}/`

**Permissions:** Must be the service owner (artist)

**Response:** `204 No Content`

**Note:** This performs a soft delete by setting `is_active=False`

---

## Bookings Endpoints

### 1. List Bookings

**Endpoint:** `GET /bookings/bookings/`

**Description:** List bookings. Clients see their own bookings, artists see bookings for them.

**Query Parameters:**
- `status` (string): Filter by status (pending, accepted, rejected, completed, cancelled)
- `booking_date` (date): Filter by booking date
- `artist` (UUID): Filter by artist ID
- `service` (UUID): Filter by service ID
- `search` (string): Search in booking_number, location
- `ordering` (string): Order by fields (booking_date, created_at, start_time)
- `page` (int): Page number

**Response:** `200 OK`
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "booking_number": "BK20260217100000ABC123",
      "client": "client-uuid",
      "client_name": "John Smith",
      "client_email": "john@example.com",
      "artist": "artist-uuid",
      "artist_name": "Jane Doe",
      "artist_photo": "https://cloudinary.com/...",
      "service": "service-uuid",
      "service_name": "Bridal Makeup",
      "booking_date": "2026-03-15",
      "start_time": "10:00:00",
      "end_time": "12:00:00",
      "status": "pending",
      "status_display": "Pending",
      "location": "123 Main St, City",
      "total_price": "150.00",
      "created_at": "2026-02-17T10:00:00Z",
      "can_review": false,
      "is_upcoming": false
    }
  ]
}
```

### 2. Create Booking (Clients Only)

**Endpoint:** `POST /bookings/bookings/`

**Permissions:** Client role required

**Request Body:**
```json
{
  "artist": "artist-uuid",
  "service": "service-uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "location": "123 Main St, City",
  "client_notes": "Please bring extra makeup"
}
```

**Validation:**
- Booking date must be in the future
- End time must be after start time
- Service must belong to the artist
- Artist must be available at the requested time
- No conflicting bookings

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "booking_number": "BK20260217100000ABC123",
  "client": "client-uuid",
  "client_name": "John Smith",
  "client_email": "john@example.com",
  "client_phone": "+1234567890",
  "artist": "artist-uuid",
  "artist_name": "Jane Doe",
  "artist_email": "jane@example.com",
  "artist_phone": "+0987654321",
  "artist_photo": "https://cloudinary.com/...",
  "service": "service-uuid",
  "service_details": {
    "id": "service-uuid",
    "name": "Bridal Makeup",
    "price": "150.00",
    "duration_minutes": 120
  },
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "status": "pending",
  "status_display": "Pending",
  "location": "123 Main St, City",
  "client_notes": "Please bring extra makeup",
  "artist_notes": null,
  "cancellation_reason": null,
  "cancelled_by": null,
  "total_price": "150.00",
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "accepted_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "can_review": false,
  "is_upcoming": false
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "The artist is not available at the selected date and time. Please choose a different time slot."
}
```

### 3. Get Booking Detail

**Endpoint:** `GET /bookings/bookings/{id}/`

**Permissions:** Must be the client or artist of the booking

**Response:** `200 OK` (same structure as create response)

### 4. Accept Booking (Artists Only)

**Endpoint:** `POST /bookings/bookings/{id}/accept/`

**Permissions:** Must be the artist of the booking

**Request Body:** (Optional)
```json
{
  "reason": "Looking forward to working with you!"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "booking_number": "BK20260217100000ABC123",
  "status": "accepted",
  "status_display": "Accepted",
  "accepted_at": "2026-02-17T11:00:00Z",
  ...
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Only pending bookings can be accepted."
}
```

### 5. Reject Booking (Artists Only)

**Endpoint:** `POST /bookings/bookings/{id}/reject/`

**Permissions:** Must be the artist of the booking

**Request Body:** (Optional)
```json
{
  "reason": "Not available at this time"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "booking_number": "BK20260217100000ABC123",
  "status": "rejected",
  "status_display": "Rejected",
  "artist_notes": "Not available at this time",
  ...
}
```

### 6. Complete Booking (Artists Only)

**Endpoint:** `POST /bookings/bookings/{id}/complete/`

**Permissions:** Must be the artist of the booking

**Request Body:** (Optional)
```json
{
  "reason": "Service completed successfully"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "booking_number": "BK20260217100000ABC123",
  "status": "completed",
  "status_display": "Completed",
  "completed_at": "2026-03-15T13:00:00Z",
  ...
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Only accepted bookings can be marked as completed."
}
```

### 7. Cancel Booking

**Endpoint:** `POST /bookings/bookings/{id}/cancel/`

**Permissions:** Must be the client or artist of the booking

**Request Body:** (Optional)
```json
{
  "reason": "Change of plans"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "booking_number": "BK20260217100000ABC123",
  "status": "cancelled",
  "status_display": "Cancelled",
  "cancelled_by": "client",
  "cancellation_reason": "Change of plans",
  "cancelled_at": "2026-02-17T12:00:00Z",
  ...
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Cannot cancel completed or already cancelled bookings."
}
```

### 8. Check Availability

**Endpoint:** `POST /bookings/bookings/check_availability/`

**Description:** Check if an artist is available for a specific date and time.

**Request Body:**
```json
{
  "artist_id": "artist-uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00"
}
```

**Response:** `200 OK`
```json
{
  "available": true,
  "artist_id": "artist-uuid",
  "artist_name": "Jane Doe",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00"
}
```

**Response (Not Available):** `200 OK`
```json
{
  "available": false,
  "reason": "Artist is not available on Wednesdays.",
  "artist_id": "artist-uuid",
  "booking_date": "2026-03-15",
  "start_time": "10:00:00",
  "end_time": "12:00:00"
}
```

### 9. Get Available Time Slots

**Endpoint:** `GET /bookings/bookings/available_slots/`

**Description:** Get all available time slots for an artist on a specific date.

**Query Parameters:**
- `artist_id` (UUID, required): Artist ID
- `booking_date` (date, required): Date in YYYY-MM-DD format
- `duration_minutes` (int, optional): Duration of service (default: 60)

**Example:**
```
GET /bookings/bookings/available_slots/?artist_id=uuid&booking_date=2026-03-15&duration_minutes=120
```

**Response:** `200 OK`
```json
{
  "artist_id": "artist-uuid",
  "artist_name": "Jane Doe",
  "booking_date": "2026-03-15",
  "duration_minutes": 120,
  "available_slots": [
    {
      "start_time": "09:00",
      "end_time": "11:00"
    },
    {
      "start_time": "09:30",
      "end_time": "11:30"
    },
    {
      "start_time": "13:00",
      "end_time": "15:00"
    }
  ],
  "total_slots": 3
}
```

### 10. Get Booking Statistics

**Endpoint:** `GET /bookings/bookings/statistics/`

**Description:** Get booking statistics for the current user.

**Response:** `200 OK`
```json
{
  "total_bookings": 25,
  "pending": 3,
  "accepted": 5,
  "completed": 15,
  "cancelled": 2,
  "rejected": 0,
  "total_revenue": 2250.00,
  "average_booking_value": 150.00
}
```

---

## Status Flow

```
PENDING → ACCEPTED → COMPLETED
    ↓         ↓
REJECTED   CANCELLED
```

**Status Descriptions:**
- `pending`: Booking created, waiting for artist to accept/reject
- `accepted`: Artist has accepted the booking
- `rejected`: Artist has rejected the booking
- `completed`: Booking has been completed
- `cancelled`: Booking has been cancelled by client or artist

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message describing the issue"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Webhook Events (Future)

The following events trigger notifications via Celery tasks:

- `booking.created` - New booking created
- `booking.accepted` - Booking accepted by artist
- `booking.rejected` - Booking rejected by artist
- `booking.completed` - Booking marked as completed
- `booking.cancelled` - Booking cancelled
- `booking.reminder` - 24-hour reminder before booking

---

## Rate Limiting

- Authenticated users: 1000 requests/hour
- Anonymous users: 100 requests/hour
- Auth endpoints: 5 requests/minute

---

## Pagination

All list endpoints support cursor-based pagination:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/bookings/?cursor=cD0yMDI2LTAyLTE3",
  "previous": null,
  "results": [...]
}
```

Default page size: 20 items
