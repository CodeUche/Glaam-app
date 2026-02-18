# GlamConnect — System Architecture

## Overview

GlamConnect is a marketplace platform connecting makeup artists with clients,
following an Uber-like service-booking model.

---

## System Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│   │  React Native │  │   Next.js    │  │   Admin      │             │
│   │  Mobile App   │  │   Web App    │  │   Dashboard  │             │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└──────────┼─────────────────┼─────────────────┼──────────────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LOAD BALANCER (Nginx)                          │
│                    SSL Termination / Rate Limiting                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Django App    │ │   Django App    │ │   Django App    │
│   Instance 1   │ │   Instance 2   │ │   Instance N   │
│   (Gunicorn)   │ │   (Gunicorn)   │ │   (Gunicorn)   │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │     Redis       │ │   Cloudinary    │
│   (Primary DB)  │ │  Cache/Queue    │ │   / AWS S3      │
│                 │ │  + WebSocket    │ │  (Media Store)  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
           ┌──────────────┐  ┌──────────────┐
           │  Celery       │  │  Django       │
           │  Workers      │  │  Channels    │
           │  (Background) │  │  (WebSocket) │
           └──────────────┘  └──────────────┘
```

## Component Responsibilities

### API Layer (Django REST Framework)
- RESTful API for all CRUD operations
- JWT authentication with refresh tokens
- Role-based access control (Client, Artist, Admin)
- Input validation, rate limiting, pagination

### Real-Time Layer (Django Channels)
- WebSocket connections for booking status updates
- Real-time notifications
- Online/offline status for artists

### Background Jobs (Celery + Redis)
- Email sending (booking confirmations, reminders)
- Image optimization after upload
- Rating recalculation
- Push notification dispatch
- Scheduled availability cleanup

### Data Layer
- PostgreSQL: Primary data store (users, bookings, reviews)
- Redis: Session cache, API response cache, Celery broker
- Cloudinary/S3: Portfolio images, profile photos

### CDN & Media
- Cloudinary transformations for image optimization
- Multiple image sizes generated on upload
- Lazy loading on frontend

---

## API Design Principles
- RESTful with consistent naming
- Versioned endpoints (`/api/v1/`)
- Standard error responses
- Cursor-based pagination for large lists
- Rate limiting per endpoint category
- HATEOAS links where useful

## Security Layers
1. **Network**: Nginx rate limiting, SSL/TLS
2. **Application**: Django middleware (CSRF, XSS, clickjacking)
3. **Authentication**: JWT with short-lived access tokens
4. **Authorization**: Object-level permissions on every view
5. **Data**: Input validation, parameterized queries, file validation
6. **Audit**: Request logging, action audit trail

---

## Database Schema

### Core Models

#### 1. User (extends Django AbstractUser)
```sql
users_user
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE, INDEXED)
├── password (VARCHAR, hashed)
├── first_name (VARCHAR)
├── last_name (VARCHAR)
├── phone_number (VARCHAR, NULL)
├── role (VARCHAR) → ['client', 'artist', 'admin']
├── is_active (BOOLEAN, default=True)
├── is_verified (BOOLEAN, default=False)
├── last_login (DATETIME)
├── created_at (DATETIME, INDEXED)
├── updated_at (DATETIME)
└── deleted_at (DATETIME, NULL) → soft delete
```

#### 2. ClientProfile
```sql
profiles_clientprofile
├── id (UUID, PK)
├── user_id (FK → users_user, UNIQUE)
├── profile_photo (VARCHAR, URL)
├── bio (TEXT, NULL)
├── preferred_location (VARCHAR, NULL)
├── notification_preferences (JSONB)
├── created_at (DATETIME)
└── updated_at (DATETIME)
```

#### 3. MakeupArtistProfile
```sql
profiles_makeupartistprofile
├── id (UUID, PK)
├── user_id (FK → users_user, UNIQUE)
├── profile_photo (VARCHAR, URL)
├── bio (TEXT)
├── specialties (ARRAY[VARCHAR]) → ['bridal', 'editorial', 'sfx', etc.]
├── years_of_experience (INTEGER)
├── hourly_rate (DECIMAL)
├── location (VARCHAR)
├── latitude (DECIMAL, NULL)
├── longitude (DECIMAL, NULL)
├── is_available (BOOLEAN, default=True)
├── average_rating (DECIMAL, default=0.0, INDEXED)
├── total_reviews (INTEGER, default=0)
├── total_bookings (INTEGER, default=0)
├── verified (BOOLEAN, default=False)
├── verification_date (DATETIME, NULL)
├── created_at (DATETIME)
└── updated_at (DATETIME)

INDEXES:
  - (average_rating, created_at)
  - (location, is_available)
  - (specialties) → GIN index for array search
```

#### 4. PortfolioImage
```sql
portfolio_portfolioimage
├── id (UUID, PK)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── image_url (VARCHAR)
├── thumbnail_url (VARCHAR)
├── caption (TEXT, NULL)
├── category (VARCHAR) → ['bridal', 'editorial', 'natural', etc.]
├── display_order (INTEGER, default=0)
├── is_featured (BOOLEAN, default=False)
├── created_at (DATETIME, INDEXED)
└── updated_at (DATETIME)

INDEXES:
  - (artist_id, display_order)
  - (artist_id, is_featured)
```

#### 5. Service
```sql
services_service
├── id (UUID, PK)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── name (VARCHAR)
├── description (TEXT)
├── price (DECIMAL)
├── duration_minutes (INTEGER)
├── category (VARCHAR)
├── is_active (BOOLEAN, default=True)
├── created_at (DATETIME)
└── updated_at (DATETIME)

INDEXES:
  - (artist_id, is_active)
```

#### 6. Availability
```sql
availability_availability
├── id (UUID, PK)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── day_of_week (INTEGER) → 0=Monday, 6=Sunday
├── start_time (TIME)
├── end_time (TIME)
├── is_active (BOOLEAN, default=True)
├── created_at (DATETIME)
└── updated_at (DATETIME)

INDEXES:
  - (artist_id, day_of_week, is_active)
```

#### 7. AvailabilityException
```sql
availability_availabilityexception
├── id (UUID, PK)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── date (DATE)
├── is_available (BOOLEAN) → False=blocked, True=special availability
├── start_time (TIME, NULL)
├── end_time (TIME, NULL)
├── reason (TEXT, NULL)
├── created_at (DATETIME)
└── updated_at (DATETIME)

INDEXES:
  - (artist_id, date)
```

#### 8. Booking
```sql
bookings_booking
├── id (UUID, PK)
├── booking_number (VARCHAR, UNIQUE, INDEXED)
├── client_id (FK → users_user, INDEXED)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── service_id (FK → services_service)
├── booking_date (DATE, INDEXED)
├── start_time (TIME)
├── end_time (TIME)
├── status (VARCHAR, INDEXED) → ['pending', 'accepted', 'rejected', 'completed', 'cancelled']
├── location (VARCHAR)
├── client_notes (TEXT, NULL)
├── artist_notes (TEXT, NULL)
├── cancellation_reason (TEXT, NULL)
├── cancelled_by (VARCHAR, NULL) → ['client', 'artist']
├── total_price (DECIMAL)
├── created_at (DATETIME, INDEXED)
├── updated_at (DATETIME)
├── accepted_at (DATETIME, NULL)
├── completed_at (DATETIME, NULL)
└── cancelled_at (DATETIME, NULL)

INDEXES:
  - (client_id, status, created_at)
  - (artist_id, status, booking_date)
  - (booking_date, status)
  - (booking_number) → UNIQUE

CONSTRAINTS:
  - CHECK (end_time > start_time)
  - CHECK (booking_date >= CURRENT_DATE)
```

#### 9. Review
```sql
reviews_review
├── id (UUID, PK)
├── booking_id (FK → bookings_booking, UNIQUE, INDEXED)
├── client_id (FK → users_user, INDEXED)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── rating (INTEGER) → 1-5
├── comment (TEXT)
├── is_visible (BOOLEAN, default=True)
├── flagged (BOOLEAN, default=False)
├── artist_response (TEXT, NULL)
├── responded_at (DATETIME, NULL)
├── created_at (DATETIME, INDEXED)
└── updated_at (DATETIME)

INDEXES:
  - (artist_id, is_visible, created_at)
  - (booking_id) → UNIQUE to prevent duplicate reviews

CONSTRAINTS:
  - CHECK (rating >= 1 AND rating <= 5)
  - UNIQUE (booking_id) → one review per booking
```

#### 10. Favorite
```sql
favorites_favorite
├── id (UUID, PK)
├── client_id (FK → users_user, INDEXED)
├── artist_id (FK → profiles_makeupartistprofile, INDEXED)
├── created_at (DATETIME)

INDEXES:
  - UNIQUE (client_id, artist_id)
  - (client_id, created_at)
```

#### 11. Notification
```sql
notifications_notification
├── id (UUID, PK)
├── user_id (FK → users_user, INDEXED)
├── notification_type (VARCHAR) → ['booking_request', 'booking_accepted', etc.]
├── title (VARCHAR)
├── message (TEXT)
├── related_booking_id (FK → bookings_booking, NULL)
├── is_read (BOOLEAN, default=False, INDEXED)
├── is_sent (BOOLEAN, default=False)
├── sent_at (DATETIME, NULL)
├── created_at (DATETIME)

INDEXES:
  - (user_id, is_read, created_at)
  - (related_booking_id)
```

#### 12. Payment (Scaffold)
```sql
payments_payment
├── id (UUID, PK)
├── booking_id (FK → bookings_booking, UNIQUE)
├── client_id (FK → users_user)
├── artist_id (FK → profiles_makeupartistprofile)
├── amount (DECIMAL)
├── currency (VARCHAR, default='USD')
├── payment_method (VARCHAR) → ['card', 'wallet', 'bank']
├── transaction_id (VARCHAR, NULL)
├── status (VARCHAR) → ['pending', 'completed', 'refunded', 'failed']
├── payment_gateway (VARCHAR, NULL) → ['stripe', 'paypal', etc.]
├── gateway_response (JSONB, NULL)
├── refund_amount (DECIMAL, default=0)
├── refunded_at (DATETIME, NULL)
├── created_at (DATETIME)
└── updated_at (DATETIME)

INDEXES:
  - (booking_id) → UNIQUE
  - (client_id, created_at)
  - (artist_id, status, created_at)
```

#### 13. AuditLog
```sql
audit_auditlog
├── id (UUID, PK)
├── user_id (FK → users_user, NULL, INDEXED)
├── action (VARCHAR) → ['login', 'booking_create', 'review_create', etc.]
├── resource_type (VARCHAR) → ['booking', 'review', 'user', etc.]
├── resource_id (UUID, NULL)
├── ip_address (VARCHAR)
├── user_agent (TEXT)
├── changes (JSONB, NULL) → old/new values
├── created_at (DATETIME, INDEXED)

INDEXES:
  - (user_id, created_at)
  - (resource_type, resource_id)
  - (created_at) → partitioned by month for performance
```

#### 14. RefreshToken
```sql
auth_refreshtoken
├── id (UUID, PK)
├── user_id (FK → users_user, INDEXED)
├── token (VARCHAR, UNIQUE, INDEXED)
├── expires_at (DATETIME, INDEXED)
├── revoked (BOOLEAN, default=False)
├── created_at (DATETIME)
└── revoked_at (DATETIME, NULL)

INDEXES:
  - (token, revoked, expires_at)
  - (user_id, revoked)
```

### Database Optimization Strategies

1. **Indexing Strategy**
   - Primary keys on all tables (UUID)
   - Foreign keys indexed automatically
   - Composite indexes on common filter combinations
   - GIN indexes for JSONB and array fields

2. **Partitioning**
   - AuditLog partitioned by month
   - Notifications partitioned by quarter (optional)

3. **Caching Strategy**
   - Artist profiles cached for 5 minutes
   - Search results cached for 2 minutes
   - Average ratings cached for 1 hour
   - Cache invalidation on updates

4. **Query Optimization**
   - Use select_related() for foreign keys
   - Use prefetch_related() for reverse lookups
   - Implement pagination (cursor-based for large datasets)
   - Use database aggregations instead of Python loops

5. **Soft Deletes**
   - Users have deleted_at field
   - Excluded from queries with manager defaults
   - Retain for audit/compliance

---

## Data Relationships

```
User (Client) 1──→∞ Booking
User (Client) 1──→∞ Favorite
User (Client) 1──→∞ Review
User (Client) 1──→1 ClientProfile

User (Artist) 1──→1 MakeupArtistProfile
MakeupArtistProfile 1──→∞ Service
MakeupArtistProfile 1──→∞ PortfolioImage
MakeupArtistProfile 1──→∞ Booking
MakeupArtistProfile 1──→∞ Availability
MakeupArtistProfile 1──→∞ Review

Booking 1──→1 Service
Booking 1──→0..1 Review
Booking 1──→0..1 Payment

User 1──→∞ Notification
User 1──→∞ RefreshToken
User 1──→∞ AuditLog
```

---

## API Endpoint Structure

### Authentication (`/api/v1/auth/`)
- `POST /register/` - Register new user
- `POST /login/` - Login and get JWT tokens
- `POST /logout/` - Revoke refresh token
- `POST /refresh/` - Refresh access token
- `POST /password/reset/` - Request password reset
- `POST /password/reset/confirm/` - Confirm password reset
- `GET /me/` - Get current user profile

### Artists (`/api/v1/artists/`)
- `GET /` - List artists (with filters)
- `GET /:id/` - Get artist detail
- `GET /:id/portfolio/` - Get portfolio images
- `GET /:id/reviews/` - Get artist reviews
- `GET /:id/services/` - Get artist services
- `GET /:id/availability/` - Get availability
- `PATCH /:id/` - Update artist profile (owner only)
- `POST /:id/portfolio/` - Add portfolio image (owner only)
- `DELETE /:id/portfolio/:imageId/` - Delete portfolio image

### Services (`/api/v1/services/`)
- `GET /` - List all services (filtered by artist)
- `POST /` - Create service (artist only)
- `PATCH /:id/` - Update service
- `DELETE /:id/` - Delete service

### Bookings (`/api/v1/bookings/`)
- `GET /` - List user's bookings
- `POST /` - Create booking (client only)
- `GET /:id/` - Get booking detail
- `PATCH /:id/accept/` - Accept booking (artist only)
- `PATCH /:id/reject/` - Reject booking (artist only)
- `PATCH /:id/complete/` - Mark complete (artist only)
- `PATCH /:id/cancel/` - Cancel booking
- `GET /check-availability/` - Check artist availability

### Reviews (`/api/v1/reviews/`)
- `POST /` - Create review (client, completed booking only)
- `GET /` - List reviews
- `GET /:id/` - Get review detail
- `PATCH /:id/respond/` - Artist response
- `DELETE /:id/` - Delete review (admin only)

### Favorites (`/api/v1/favorites/`)
- `GET /` - List user's favorites
- `POST /` - Add to favorites
- `DELETE /:id/` - Remove from favorites

### Notifications (`/api/v1/notifications/`)
- `GET /` - List user's notifications
- `PATCH /:id/read/` - Mark as read
- `PATCH /read-all/` - Mark all as read

### Search (`/api/v1/search/`)
- `GET /artists/` - Search artists with filters

### Admin (`/api/v1/admin/`)
- `GET /users/` - List all users
- `PATCH /users/:id/suspend/` - Suspend user
- `GET /analytics/` - Platform analytics
- `GET /reviews/flagged/` - Flagged reviews

---

## Real-Time Events (WebSocket)

### Connection URL
`ws://domain.com/ws/notifications/?token=<jwt_token>`

### Event Types

**Sent to Client:**
```json
{
  "type": "booking.created",
  "data": {
    "booking_id": "uuid",
    "artist_name": "Jane Doe",
    "date": "2026-03-15",
    "time": "10:00"
  }
}

{
  "type": "booking.accepted",
  "data": {
    "booking_id": "uuid",
    "message": "Your booking has been accepted!"
  }
}

{
  "type": "booking.rejected",
  "data": {
    "booking_id": "uuid",
    "message": "Your booking was declined."
  }
}

{
  "type": "artist.status",
  "data": {
    "artist_id": "uuid",
    "is_available": true
  }
}
```

---

## Technology Stack Details

### Backend Dependencies
```
Django==5.0+
djangorestframework==3.14+
djangorestframework-simplejwt==5.3+
django-cors-headers==4.3+
django-filter==23.5+
channels==4.0+
channels-redis==4.1+
celery==5.3+
redis==5.0+
psycopg2-binary==2.9+
Pillow==10.2+
cloudinary==1.36+
django-environ==0.11+
gunicorn==21.2+
whitenoise==6.6+
django-ratelimit==4.1+
```

### Frontend Dependencies (Next.js)
```
next==14+
react==18+
react-dom==18+
typescript==5+
tailwindcss==3+
axios==1.6+
socket.io-client==4.6+
react-hook-form==7.49+
zod==3.22+
react-query==5+
zustand==4.4+
```

### Frontend Dependencies (React Native)
```
react-native==0.73+
@react-navigation/native==6+
@react-navigation/stack==6+
axios==1.6+
socket.io-client==4.6+
react-native-vector-icons==10+
react-native-image-picker==7+
react-native-maps==1.10+
@react-native-async-storage/async-storage==1.21+
```

---

## Environment Variables

### Backend (.env)
```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/glamconnect

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=your-cloud-name
```

---

## Deployment Architecture

### Production Setup
```
┌─────────────────────────────────────────┐
│          Domain: glamconnect.com         │
├─────────────────────────────────────────┤
│  - app.glamconnect.com → Next.js App    │
│  - api.glamconnect.com → Django API     │
│  - admin.glamconnect.com → Admin Panel  │
└─────────────────────────────────────────┘
```

### Docker Services
- `web` - Django + Gunicorn
- `db` - PostgreSQL 15
- `redis` - Redis 7
- `celery_worker` - Background tasks
- `celery_beat` - Scheduled tasks
- `nginx` - Reverse proxy + static files
- `frontend` - Next.js (optional, can be separate)
