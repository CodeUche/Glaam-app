# GlamConnect Profiles App - Quick Start Guide

## Installation & Setup

### 1. Dependencies
Ensure these packages are installed:
```bash
pip install django djangorestframework django-filter django-redis cloudinary psycopg2-binary
```

### 2. Database Migration
```bash
python manage.py makemigrations profiles
python manage.py migrate profiles
```

### 3. Create Test Data
```python
# In Django shell (python manage.py shell)
from apps.users.models import User
from apps.profiles.models import MakeupArtistProfile, ClientProfile, PortfolioImage

# Create a client
client_user = User.objects.create_user(
    email='client@example.com',
    password='password123',
    first_name='John',
    last_name='Doe',
    role='client'
)
client_profile = ClientProfile.objects.create(
    user=client_user,
    bio='Looking for the best makeup artists',
    preferred_location='Lagos, Nigeria'
)

# Create an artist
artist_user = User.objects.create_user(
    email='artist@example.com',
    password='password123',
    first_name='Jane',
    last_name='Beauty',
    role='artist'
)
artist_profile = MakeupArtistProfile.objects.create(
    user=artist_user,
    bio='Professional makeup artist with 5 years experience',
    specialties=['bridal', 'glam'],
    years_of_experience=5,
    hourly_rate=7500,
    location='Lagos, Nigeria',
    latitude=6.5244,
    longitude=3.3792,
    is_available=True
)
```

## Quick API Test

### 1. Get JWT Token
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "artist@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

### 2. List Artists (Public - No Auth Required)
```bash
curl http://localhost:8000/api/profiles/artists/
```

### 3. Get Artist Detail (Cached)
```bash
curl http://localhost:8000/api/profiles/artists/{artist_id}/
```

### 4. Search Artists
```bash
# Find bridal artists in Lagos with 4+ rating
curl "http://localhost:8000/api/profiles/artists/?location=Lagos&specialty=bridal&min_rating=4.0"

# Search by name
curl "http://localhost:8000/api/profiles/artists/?search=Jane"

# Filter by price range
curl "http://localhost:8000/api/profiles/artists/?price_range=moderate&ordering=-rating"
```

### 5. Update Own Profile (Auth Required)
```bash
curl -X PATCH http://localhost:8000/api/profiles/artists/me/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "hourly_rate": 8000,
    "is_available": true
  }'
```

### 6. Upload Portfolio Image (Artist Only)
```bash
curl -X POST http://localhost:8000/api/profiles/portfolio/ \
  -H "Authorization: Bearer <access_token>" \
  -F "image_url=@/path/to/image.jpg" \
  -F "category=bridal" \
  -F "caption=Beautiful bridal makeup" \
  -F "is_featured=true"
```

### 7. Toggle Favorite (Auth Required)
```bash
curl -X POST http://localhost:8000/api/profiles/artists/{artist_id}/toggle_favorite/ \
  -H "Authorization: Bearer <access_token>"
```

### 8. Set Availability (Artist Only)
```bash
curl -X POST http://localhost:8000/api/profiles/availability/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "is_active": true
  }'
```

## Common Use Cases

### Use Case 1: Client Searching for Bridal Artist
```python
# In frontend (JavaScript/React)
const searchArtists = async () => {
  const response = await fetch(
    '/api/profiles/artists/?specialty=bridal&location=Lagos&min_rating=4.0&ordering=-rating'
  );
  const data = await response.json();
  return data.results;
};
```

### Use Case 2: Artist Updating Availability
```python
# In frontend
const updateAvailability = async (token) => {
  const response = await fetch('/api/profiles/availability/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      day_of_week: 1, // Tuesday
      start_time: '09:00',
      end_time: '17:00',
      is_active: true
    })
  });
  return await response.json();
};
```

### Use Case 3: Client Adding to Favorites
```python
# In frontend
const toggleFavorite = async (artistId, token) => {
  const response = await fetch(`/api/profiles/artists/${artistId}/toggle_favorite/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
};
```

### Use Case 4: Artist Managing Portfolio
```python
# Upload image
const uploadPortfolioImage = async (file, token) => {
  const formData = new FormData();
  formData.append('image_url', file);
  formData.append('category', 'bridal');
  formData.append('caption', 'Beautiful bridal makeup');
  formData.append('is_featured', 'true');

  const response = await fetch('/api/profiles/portfolio/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  return await response.json();
};

// Reorder images
const reorderPortfolio = async (imageIds, token) => {
  const response = await fetch('/api/profiles/portfolio/reorder/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ image_ids: imageIds })
  });
  return await response.json();
};
```

## Cache Management

### Check Cache Status (Django Shell)
```python
from django.core.cache import cache

# Get cache keys
keys = cache.keys('artist_*')
print(f"Total cached items: {len(keys)}")

# Clear specific cache
cache.delete('artist_detail:artist_id=<uuid>:user_id=anonymous')

# Clear all artist caches
cache.delete_pattern('artist_*')
```

### Monitor Cache Performance
```python
# Add to views for debugging
import time
start = time.time()

# Your cached view logic
cached_data = cache.get(cache_key)

duration = time.time() - start
print(f"Cache lookup took {duration:.4f} seconds")
```

## Testing

### Run Tests
```bash
# All profiles tests
python manage.py test apps.profiles

# Specific test class
python manage.py test apps.profiles.tests.MakeupArtistProfileTests

# With coverage
coverage run --source='apps.profiles' manage.py test apps.profiles
coverage report
```

### Test in Django Shell
```python
from apps.profiles.models import MakeupArtistProfile
from apps.profiles.serializers import MakeupArtistListSerializer
from django.core.cache import cache

# Test query optimization
artists = MakeupArtistProfile.objects.select_related('user').prefetch_related('portfolio_images')
print(artists.query)  # View SQL query

# Test serializer
artist = artists.first()
serializer = MakeupArtistListSerializer(artist)
print(serializer.data)

# Test cache
cache.set('test_key', {'data': 'value'}, 60)
print(cache.get('test_key'))
```

## Admin Interface

Access at: http://localhost:8000/admin/

### Create Superuser
```bash
python manage.py createsuperuser
```

### Admin Features
- Manage all profiles
- View statistics
- Verify artists
- Mark availability
- View portfolio images
- Bulk operations

## Troubleshooting

### Issue: Cache Not Working
**Solution:**
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Restart Redis
redis-server

# Check Django cache settings
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')  # Should return 'value'
```

### Issue: Images Not Uploading
**Solution:**
```python
# Check Cloudinary configuration in settings.py
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': env('CLOUDINARY_API_KEY'),
    'API_SECRET': env('CLOUDINARY_API_SECRET')
}
```

### Issue: Filtering Not Working
**Solution:**
```python
# Ensure django-filter is installed and configured
INSTALLED_APPS = [
    ...
    'django_filters',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ]
}
```

### Issue: Permission Denied
**Solution:**
- Check user role matches required permission
- Verify JWT token is valid
- Ensure user owns the resource for owner-only actions

## Performance Tips

### 1. Database Indexes
Already implemented on:
- `average_rating`
- `is_available`
- `location`
- Compound indexes for common queries

### 2. Query Optimization
```python
# Good - Uses select_related
artists = MakeupArtistProfile.objects.select_related('user')

# Bad - N+1 queries
artists = MakeupArtistProfile.objects.all()
for artist in artists:
    print(artist.user.email)  # Separate query each time
```

### 3. Caching Strategy
- List views: 5 minutes
- Detail views: 10 minutes
- Invalidate on write operations
- Use Redis for production

### 4. Pagination
```python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}
```

## Environment Variables

Required in `.env`:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/glamconnect

# Redis
REDIS_URL=redis://localhost:6379/0

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Deployment Checklist

Before deploying:
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up Redis server
- [ ] Configure Cloudinary
- [ ] Run migrations
- [ ] Collect static files
- [ ] Set up HTTPS
- [ ] Configure CORS
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups

## Support & Resources

- **Documentation:** See IMPLEMENTATION.md and API_REFERENCE.md
- **Django Docs:** https://docs.djangoproject.com/
- **DRF Docs:** https://www.django-rest-framework.org/
- **Redis Cache:** https://github.com/jazzband/django-redis

## Quick Reference

### Common Commands
```bash
# Run server
python manage.py runserver

# Run tests
python manage.py test apps.profiles

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

### Import Paths
```python
from apps.profiles.models import MakeupArtistProfile, ClientProfile
from apps.profiles.serializers import MakeupArtistListSerializer
from apps.profiles.permissions import IsArtist, CanManagePortfolio
from apps.profiles.filters import MakeupArtistFilter
```

## Getting Help

If you encounter issues:
1. Check the error logs
2. Review the documentation files
3. Test in Django shell
4. Check Redis connection
5. Verify permissions
6. Review request headers/body

Happy coding! 🎨✨
