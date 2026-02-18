# Services App Integration Guide

This guide helps you integrate the services app into your GlamConnect Django project.

## Step 1: Add App to INSTALLED_APPS

In `backend/config/settings.py`, add the services app to INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ... other apps
    'apps.users',
    'apps.profiles',
    'apps.services',  # Add this line
    'apps.bookings',
    'apps.reviews',
    # ... other apps
]
```

## Step 2: Include URLs

In your main `urls.py` (e.g., `backend/config/urls.py`), include the services URLs:

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('api/users/', include('apps.users.urls')),
    path('api/services/', include('apps.services.urls')),  # Add this line
    # ... other URLs
]
```

## Step 3: Run Migrations

Create and apply migrations for the services app:

```bash
# Create migrations
python manage.py makemigrations services

# Apply migrations
python manage.py migrate services
```

## Step 4: Register Admin (Optional)

The admin is already registered in `admin.py`. Ensure your admin site is properly configured in your main URLs.

## Step 5: Test the API

Start the development server:

```bash
python manage.py runserver
```

### Test Endpoints

1. **List Services:**
   ```
   GET http://localhost:8000/api/services/
   ```

2. **Create Service (as artist):**
   ```
   POST http://localhost:8000/api/services/
   Headers: Authorization: Bearer {access_token}
   Body:
   {
       "name": "Bridal Makeup Package",
       "description": "Complete bridal makeup service",
       "category": "bridal",
       "price": "250.00",
       "duration": 120
   }
   ```

3. **Get My Services:**
   ```
   GET http://localhost:8000/api/services/my_services/
   Headers: Authorization: Bearer {access_token}
   ```

4. **Get Categories:**
   ```
   GET http://localhost:8000/api/services/categories/
   ```

## Step 6: Dependencies

Ensure these packages are installed:

```bash
pip install djangorestframework
pip install django-filter
```

Add to `INSTALLED_APPS` if not already added:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'django_filters',
    # ...
]
```

Configure DRF settings:

```python
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # ... other settings
}
```

## Step 7: Permissions Configuration

Ensure proper authentication is configured in your DRF settings:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # ... other settings
}
```

## Step 8: Database Indexes

The Service model includes several database indexes for optimization. After running migrations, you can verify indexes:

```bash
python manage.py dbshell
# Then in the database shell:
\d services_service  # PostgreSQL
SHOW INDEX FROM services_service;  # MySQL
```

## Common Issues

### Issue 1: MakeupArtistProfile Not Found

**Error:** `apps.profiles.MakeupArtistProfile does not exist`

**Solution:** Ensure the profiles app is migrated before services:
```bash
python manage.py migrate profiles
python manage.py migrate services
```

### Issue 2: Permission Denied When Creating Service

**Error:** `403 Forbidden`

**Solution:** Ensure:
1. User is authenticated
2. User has role='artist'
3. User has an associated MakeupArtistProfile

### Issue 3: Import Error for permissions

**Error:** `ImportError: cannot import name 'IsArtist'`

**Solution:** Ensure `apps.users.permissions` contains the `IsArtist` permission class.

## Testing

Run the test suite:

```bash
# Test all services app
python manage.py test apps.services

# Test specific test class
python manage.py test apps.services.tests.ServiceModelTests

# Test with verbosity
python manage.py test apps.services -v 2
```

## API Documentation

Once integrated, you can access API documentation (if using drf-spectacular or similar):

```
http://localhost:8000/api/schema/swagger-ui/
http://localhost:8000/api/schema/redoc/
```

## Next Steps

1. Create some test data through the admin interface
2. Test API endpoints with Postman or curl
3. Integrate with frontend application
4. Set up proper CORS headers for frontend access
5. Configure production settings (allowed hosts, HTTPS, etc.)

## Production Checklist

- [ ] Run migrations on production database
- [ ] Collect static files if using admin
- [ ] Set up proper database indexes
- [ ] Configure rate limiting for API
- [ ] Set up monitoring and logging
- [ ] Test all endpoints with production-like data
- [ ] Configure proper CORS settings
- [ ] Set up API documentation
- [ ] Test permission boundaries
- [ ] Verify database constraints
