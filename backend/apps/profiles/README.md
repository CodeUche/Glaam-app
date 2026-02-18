# Profiles App - GlamConnect

## Overview
The profiles app manages client and makeup artist profiles, including portfolio images, favorites, and availability schedules.

## Features

### 1. Client Profiles
- Create and manage client profiles
- Upload profile photos (Cloudinary)
- Set notification preferences
- Manage preferred locations

### 2. Makeup Artist Profiles
- Comprehensive artist profiles with bio, specialties, and rates
- Location-based services with geocoding support
- Rating and review aggregation
- Verification system
- Availability management
- Portfolio image galleries

### 3. Portfolio Management
- Upload and manage portfolio images
- Categorize images (bridal, editorial, natural, glam, SFX, etc.)
- Featured image selection
- Custom ordering/display sequences
- Thumbnail generation

### 4. Favorites System
- Clients can favorite artists
- Track favorite artists for quick access
- Prevent duplicate favorites

### 5. Availability Management
- Weekly recurring schedules
- Time slot management
- Availability exceptions for specific dates
- Block out dates or add special availability

## API Endpoints

### Client Profiles
```
GET     /api/profiles/clients/              - List client profiles (admin only)
GET     /api/profiles/clients/me/           - Get current user's profile
PUT     /api/profiles/clients/me/           - Update current user's profile
PATCH   /api/profiles/clients/me/           - Partial update current user's profile
GET     /api/profiles/clients/{id}/         - Get specific client profile
PUT     /api/profiles/clients/{id}/         - Update specific client profile
PATCH   /api/profiles/clients/{id}/         - Partial update specific client profile
```

### Makeup Artist Profiles
```
GET     /api/profiles/artists/              - List all artists (with filtering)
POST    /api/profiles/artists/              - Create artist profile (artists only)
GET     /api/profiles/artists/me/           - Get current artist's profile
PUT     /api/profiles/artists/me/           - Update current artist's profile
PATCH   /api/profiles/artists/me/           - Partial update current artist's profile
GET     /api/profiles/artists/{id}/         - Get specific artist profile
PUT     /api/profiles/artists/{id}/         - Update artist profile (owner only)
PATCH   /api/profiles/artists/{id}/         - Partial update artist profile (owner only)
DELETE  /api/profiles/artists/{id}/         - Delete artist profile (owner only)
GET     /api/profiles/artists/{id}/portfolio/ - Get artist's portfolio
GET     /api/profiles/artists/{id}/availability/ - Get artist's availability
POST    /api/profiles/artists/{id}/toggle_favorite/ - Toggle favorite status
```

### Portfolio Images
```
GET     /api/profiles/portfolio/            - List all portfolio images
POST    /api/profiles/portfolio/            - Upload portfolio image (artists only)
GET     /api/profiles/portfolio/my_portfolio/ - Get current artist's portfolio
POST    /api/profiles/portfolio/reorder/    - Reorder portfolio images
GET     /api/profiles/portfolio/{id}/       - Get specific portfolio image
PUT     /api/profiles/portfolio/{id}/       - Update portfolio image (owner only)
PATCH   /api/profiles/portfolio/{id}/       - Partial update portfolio image (owner only)
DELETE  /api/profiles/portfolio/{id}/       - Delete portfolio image (owner only)
POST    /api/profiles/portfolio/{id}/toggle_featured/ - Toggle featured status
```

### Favorites
```
GET     /api/profiles/favorites/            - List user's favorites
POST    /api/profiles/favorites/            - Add artist to favorites
GET     /api/profiles/favorites/my_favorites/ - Get current user's favorites
GET     /api/profiles/favorites/{id}/       - Get specific favorite
DELETE  /api/profiles/favorites/{id}/       - Remove from favorites
```

### Availability
```
GET     /api/profiles/availability/         - List availability slots
POST    /api/profiles/availability/         - Create availability slot (artists only)
GET     /api/profiles/availability/my_schedule/ - Get current artist's schedule
GET     /api/profiles/availability/{id}/    - Get specific availability slot
PUT     /api/profiles/availability/{id}/    - Update availability (owner only)
PATCH   /api/profiles/availability/{id}/    - Partial update availability (owner only)
DELETE  /api/profiles/availability/{id}/    - Delete availability (owner only)
```

### Availability Exceptions
```
GET     /api/profiles/availability-exceptions/ - List exceptions
POST    /api/profiles/availability-exceptions/ - Create exception (artists only)
GET     /api/profiles/availability-exceptions/my_exceptions/ - Get artist's exceptions
GET     /api/profiles/availability-exceptions/{id}/ - Get specific exception
PUT     /api/profiles/availability-exceptions/{id}/ - Update exception (owner only)
PATCH   /api/profiles/availability-exceptions/{id}/ - Partial update exception (owner only)
DELETE  /api/profiles/availability-exceptions/{id}/ - Delete exception (owner only)
```

## Filtering & Search

### Artist Filtering
The artist list endpoint supports extensive filtering:

```
GET /api/profiles/artists/?parameter=value
```

**Available Filters:**
- `location` - Filter by location (partial match)
- `location_exact` - Filter by exact location
- `min_rating` / `rating` - Minimum average rating (0-5)
- `specialty` - Filter by single specialty
- `specialties` - Filter by multiple specialties (comma-separated)
- `min_price` - Minimum hourly rate
- `max_price` - Maximum hourly rate
- `price_range` - Predefined ranges: budget (<50), moderate (50-100), premium (>100)
- `available` - Filter by availability status (true/false)
- `verified` - Filter by verification status (true/false)
- `min_experience` - Minimum years of experience
- `max_experience` - Maximum years of experience
- `experience_level` - Predefined levels: beginner (<2), intermediate (2-5), expert (>5)
- `search` - Search across name, bio, location, specialties
- `ordering` - Sort results: rating, price, experience, reviews, bookings, newest

**Example Queries:**
```
# Find verified bridal artists in New York with 4+ rating
GET /api/profiles/artists/?location=New%20York&specialty=bridal&min_rating=4&verified=true

# Find budget-friendly makeup artists available now
GET /api/profiles/artists/?price_range=budget&available=true

# Search for "wedding" and sort by rating
GET /api/profiles/artists/?search=wedding&ordering=-rating

# Find expert artists with glam or editorial specialties
GET /api/profiles/artists/?specialties=glam,editorial&experience_level=expert
```

### Portfolio Filtering
```
GET /api/profiles/portfolio/?parameter=value
```

**Available Filters:**
- `category` - Filter by category (bridal, editorial, etc.)
- `is_featured` - Filter by featured status
- `artist` - Filter by artist ID
- `ordering` - Sort by: order, newest

## Permissions

### Client Profiles
- **List**: Admin only
- **Retrieve**: Owner or admin
- **Create**: Authenticated users (automatic on registration)
- **Update**: Owner only
- **Delete**: Owner or admin

### Artist Profiles
- **List**: Public (read-only)
- **Retrieve**: Public (read-only)
- **Create**: Artists only
- **Update**: Owner only
- **Delete**: Owner only

### Portfolio Images
- **List**: Public (read-only)
- **Retrieve**: Public (read-only)
- **Create**: Artists only
- **Update**: Owner only
- **Delete**: Owner only

### Favorites
- **All operations**: Authenticated users (own favorites only)

### Availability
- **List/Retrieve**: Public (read-only)
- **Create/Update/Delete**: Artists only (own schedule only)

## Validation

### Client Profiles
- Profile photo must be valid image format (JPEG, PNG, WebP)
- Notification preferences must be a valid dictionary

### Artist Profiles
- At least one specialty required
- Years of experience: 0-50
- Hourly rate must be positive
- Location required
- Latitude/longitude must be valid coordinates (-90 to 90, -180 to 180)

### Portfolio Images
- Image required
- Display order must be non-negative
- Category must be from predefined choices

### Availability
- Start time must be before end time
- Day of week: 0-6 (Monday-Sunday)
- No overlapping time slots on the same day

### Availability Exceptions
- Date cannot be in the past
- If available, start/end times required
- Start time must be before end time

## Security Features

1. **Authentication Required**: Most write operations require authentication
2. **Ownership Verification**: Users can only modify their own data
3. **Role-Based Access**: Artists-only endpoints enforce role verification
4. **Input Validation**: Comprehensive validation on all inputs
5. **SQL Injection Prevention**: Django ORM with parameterized queries
6. **XSS Prevention**: Automatic escaping in responses
7. **Rate Limiting**: Configured in Django REST Framework settings

## Database Optimization

1. **Indexes**: Strategic indexes on frequently queried fields
2. **Select Related**: Optimized queries with select_related for foreign keys
3. **Prefetch Related**: Optimized queries for reverse relationships
4. **Cursor Pagination**: Efficient pagination for large datasets
5. **Database-Level Constraints**: Unique constraints, check constraints

## File Upload

- **Storage**: Cloudinary for all images
- **Max Size**: 5MB (configurable in settings)
- **Allowed Formats**: JPEG, PNG, WebP
- **Automatic Optimization**: Cloudinary handles compression and optimization
- **CDN Delivery**: Fast global content delivery

## Admin Interface

All models are registered in Django admin with:
- Custom list displays
- Search capabilities
- Filtering options
- Inline editing for related models
- Bulk actions
- Custom admin actions (verify artists, toggle featured, etc.)

## Testing Checklist

### Client Profiles
- [ ] Create client profile
- [ ] Upload profile photo
- [ ] Update notification preferences
- [ ] View own profile

### Artist Profiles
- [ ] Create artist profile with all required fields
- [ ] Update profile information
- [ ] Search for artists by location
- [ ] Filter by rating, price, specialty
- [ ] View artist details with portfolio

### Portfolio
- [ ] Upload portfolio images
- [ ] Categorize images
- [ ] Mark images as featured
- [ ] Reorder portfolio images
- [ ] Delete portfolio images

### Favorites
- [ ] Add artist to favorites
- [ ] Remove from favorites
- [ ] View all favorites
- [ ] Toggle favorite status

### Availability
- [ ] Set weekly availability
- [ ] Create availability exceptions
- [ ] Block out dates
- [ ] Prevent overlapping schedules

## Future Enhancements

1. **Geolocation Search**: Distance-based artist search
2. **Advanced Portfolio**: Video support, before/after galleries
3. **Social Features**: Artist following, profile sharing
4. **Analytics**: Profile views, search appearances
5. **Recommendations**: AI-powered artist recommendations
6. **Badges**: Achievement system for artists
7. **Multi-language**: i18n support for global reach
