# Reviews App Setup Guide

## Installation Steps

### 1. App is Already Registered
The reviews app is already registered in `config/settings.py`:
```python
INSTALLED_APPS = [
    ...
    'apps.reviews',
    ...
]
```

### 2. Create Database Migrations
```bash
cd c:\Users\Precious\MakeUp-app\backend
python manage.py makemigrations reviews
python manage.py migrate reviews
```

### 3. Update URL Configuration
Add reviews URLs to the main URL configuration in `config/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('api/v1/reviews/', include('apps.reviews.urls')),
    ...
]
```

### 4. Update Celery Beat Schedule (Already Done)
The Celery beat schedule in `config/celery.py` already includes:
```python
app.conf.beat_schedule = {
    ...
    'update-artist-ratings': {
        'task': 'apps.reviews.tasks.update_artist_ratings',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
}
```

Add the review reminders task if not present:
```python
'send-review-reminders': {
    'task': 'apps.reviews.tasks.send_review_reminders_batch',
    'schedule': crontab(hour=10, minute=0),  # Run daily at 10 AM
},
```

### 5. Verify Dependencies
All required packages should already be installed:
- Django REST Framework
- django-filter
- celery
- redis

If any are missing, install with:
```bash
pip install djangorestframework django-filter celery redis
```

### 6. Create Superuser (if not already done)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

### 8. Start Celery Worker (Separate Terminal)
```bash
celery -A config worker -l info
```

### 9. Start Celery Beat (Separate Terminal)
```bash
celery -A config beat -l info
```

## Testing the App

### 1. Access Django Admin
Navigate to `http://localhost:8000/admin/` and log in with superuser credentials.
You should see "Reviews" in the admin panel.

### 2. Create Test Data
Create test users, artist profiles, services, and bookings through admin or API.

### 3. Test API Endpoints

#### List Reviews
```bash
curl http://localhost:8000/api/v1/reviews/
```

#### Create Review (requires auth token)
```bash
curl -X POST http://localhost:8000/api/v1/reviews/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking": "booking-uuid",
    "rating": 5,
    "comment": "Excellent service!"
  }'
```

#### Get Review Stats
```bash
curl http://localhost:8000/api/v1/reviews/stats/?artist=artist-uuid
```

### 4. Test Management Command
```bash
python manage.py update_all_ratings --verbose
```

## Configuration

### Email Settings
Update email settings in `.env` or `settings.py` for review reminder emails:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@glamconnect.com
```

### Redis Settings
Ensure Redis is configured for Celery:
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

## Monitoring

### Check Celery Tasks
```bash
# View active tasks
celery -A config inspect active

# View scheduled tasks
celery -A config inspect scheduled

# View registered tasks
celery -A config inspect registered
```

### Check Redis
```bash
redis-cli
> KEYS *
> GET key_name
```

### Check Logs
Monitor application logs for review-related activities:
```bash
tail -f logs/app.log | grep review
```

## Common Issues

### Issue: Migrations fail
**Solution:** Ensure all dependent apps (bookings, profiles, users) are migrated first:
```bash
python manage.py migrate users
python manage.py migrate profiles
python manage.py migrate bookings
python manage.py migrate reviews
```

### Issue: Celery tasks not executing
**Solution:**
1. Ensure Redis is running: `redis-server`
2. Restart Celery worker and beat
3. Check Celery logs for errors

### Issue: Review creation fails with "booking not completed"
**Solution:**
1. Ensure the booking status is "completed"
2. Check that the user is the client of the booking
3. Verify no review already exists for the booking

### Issue: Artist ratings not updating
**Solution:**
1. Check Celery worker logs
2. Manually trigger update: `python manage.py update_all_ratings`
3. Verify signals are registered in `apps.py`

## Performance Optimization

### Database Indexes
All necessary indexes are defined in the model:
- `(artist, is_visible, created_at)` - For artist review listings
- `(booking)` - Unique constraint for one review per booking
- `(rating, created_at)` - For rating-based queries

### Query Optimization
The views use `select_related()` to minimize database queries:
```python
queryset = Review.objects.select_related(
    'client',
    'artist',
    'artist__user',
    'booking'
).all()
```

### Caching
Consider adding caching for review statistics:
```python
from django.core.cache import cache

# Cache artist stats for 5 minutes
cache_key = f'review_stats_{artist_id}'
stats = cache.get(cache_key)
if not stats:
    stats = calculate_stats(artist_id)
    cache.set(cache_key, stats, 300)
```

## API Documentation

### Generate API Schema
```bash
python manage.py generateschema --file openapi-schema.yml
```

### Access Browsable API
Navigate to `http://localhost:8000/api/v1/reviews/` in a browser to see the browsable API.

## Production Checklist

- [ ] Database migrations applied
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] Redis running and configured
- [ ] Email settings configured
- [ ] Error logging configured
- [ ] Rate limiting enabled
- [ ] CORS settings configured
- [ ] SSL/HTTPS enabled
- [ ] Admin panel secured
- [ ] Backup strategy for reviews
- [ ] Monitoring alerts configured

## Maintenance

### Regular Tasks
- Monitor flagged reviews daily
- Review spam detection accuracy weekly
- Check rating calculation accuracy monthly
- Clean up old audit logs quarterly

### Database Maintenance
```bash
# Vacuum database (PostgreSQL)
python manage.py dbshell
VACUUM ANALYZE reviews_review;

# Check review statistics
SELECT
    COUNT(*) as total_reviews,
    AVG(rating) as avg_rating,
    COUNT(DISTINCT artist_id) as artists_with_reviews
FROM reviews_review
WHERE is_visible = TRUE;
```

## Support

For issues or questions:
1. Check logs: `logs/app.log`
2. Review documentation: `README.md`
3. Check Django admin panel for data consistency
4. Run tests: `python manage.py test apps.reviews`
