# Reviews App

The reviews app handles client reviews for completed bookings in GlamConnect.

## Features

- **One Review Per Booking**: Clients can leave one review per completed booking
- **Rating System**: 1-5 star ratings with comments
- **Artist Responses**: Artists can respond to reviews
- **Spam Prevention**: Automated spam detection and manual moderation
- **Visibility Controls**: Admin can hide inappropriate reviews
- **Automatic Rating Updates**: Artist ratings are automatically recalculated when reviews change
- **Review Reminders**: Automated reminders sent 24 hours after booking completion

## Models

### Review
- `booking`: One-to-one relationship with completed booking
- `client`: The client who wrote the review
- `artist`: The artist being reviewed
- `rating`: 1-5 star rating
- `comment`: Review text from client
- `is_visible`: Controls public visibility
- `flagged`: Marked for moderation
- `artist_response`: Optional response from artist
- `responded_at`: Timestamp of artist response

## API Endpoints

### List Reviews
```
GET /api/v1/reviews/
GET /api/v1/reviews/?artist={artist_id}
GET /api/v1/reviews/?client={client_id}
GET /api/v1/reviews/?rating=5
GET /api/v1/reviews/?has_response=true
```

**Query Parameters:**
- `artist`: Filter by artist ID
- `client`: Filter by client ID
- `rating`: Filter by exact rating
- `min_rating`: Filter by minimum rating
- `max_rating`: Filter by maximum rating
- `has_response`: Filter reviews with/without artist response
- `flagged`: Filter flagged reviews
- `is_visible`: Filter visible/hidden reviews
- `created_after`: Filter by creation date
- `created_before`: Filter by creation date

### Create Review
```
POST /api/v1/reviews/
{
    "booking": "booking-uuid",
    "rating": 5,
    "comment": "Excellent service! Very professional."
}
```

**Requirements:**
- Must be authenticated as a client
- Booking must be completed
- Booking must not already have a review
- User must be the client of the booking

### Get Review Detail
```
GET /api/v1/reviews/{id}/
```

### Artist Response
```
PATCH /api/v1/reviews/{id}/respond/
{
    "response": "Thank you for your feedback!"
}
```

**Requirements:**
- Must be authenticated as an artist
- Must be the artist being reviewed

### Admin Moderation
```
PATCH /api/v1/reviews/{id}/moderate/
{
    "action": "flag|unflag|hide|show",
    "reason": "Spam content" (required for flag)
}
```

**Requirements:**
- Must be authenticated as admin

### Review Statistics
```
GET /api/v1/reviews/stats/?artist={artist_id}
```

**Returns:**
- `total_reviews`: Total number of reviews
- `average_rating`: Average rating
- `rating_distribution`: Count of each rating (1-5)
- `recent_reviews_count`: Reviews in last 30 days
- `response_rate`: Percentage of reviews with artist response

### My Reviews
```
GET /api/v1/reviews/my-reviews/
```

Returns reviews written by the current user (if client) or reviews about them (if artist).

### Flagged Reviews (Admin Only)
```
GET /api/v1/reviews/flagged/
```

## Permissions

- **Create Review**: Authenticated clients only, must have completed booking
- **View Review**: Anyone can view visible reviews; hidden reviews only visible to client, artist, or admin
- **Artist Response**: Authenticated artists only, for reviews about them
- **Moderation**: Admins only

## Validation Rules

### Review Creation
- Rating must be 1-5
- Comment must be at least 10 characters
- Comment must not exceed 2000 characters
- Booking must be completed
- No duplicate reviews per booking
- Spam detection for repetitive content

### Artist Response
- Response must be at least 10 characters
- Response must not exceed 1000 characters
- Spam detection for repetitive content

## Background Tasks

### update_artist_rating
Triggered when:
- New review created
- Review deleted
- Review visibility changed

Recalculates:
- Average rating (only visible reviews)
- Total review count

### send_review_reminder
Triggered 24 hours after booking completion.
Sends email and in-app notification to client.

### send_review_reminders_batch
Scheduled daily to send reminders for all completed bookings from previous day.

### check_review_spam
Automated spam detection checks:
- Excessive capitalization
- URLs in review
- Email addresses in review
- Rapid submission (multiple reviews in 1 hour)

### update_artist_ratings
Scheduled every 30 minutes to ensure all ratings are current.

## Signals

### post_save (Review)
- Updates artist rating
- Triggers spam detection
- Sends notification to artist
- Sends notification to client (if artist responds)

### post_delete (Review)
- Updates artist rating after deletion

### post_save (Booking)
- Schedules review reminder when booking completed

## Spam Prevention

1. **Length Validation**: Minimum and maximum character limits
2. **Repetition Detection**: Flags reviews with >70% repeated words
3. **URL Detection**: Flags reviews containing URLs
4. **Email Detection**: Flags reviews containing email addresses
5. **Rate Limiting**: Flags users submitting multiple reviews rapidly
6. **Manual Moderation**: Admin can flag/hide inappropriate content

## Testing

Run tests with:
```bash
python manage.py test apps.reviews
```

## Migrations

Create migrations with:
```bash
python manage.py makemigrations reviews
python manage.py migrate reviews
```

## Admin Interface

Admins can:
- View all reviews
- Filter by rating, visibility, flagged status
- Search reviews by content, client, or artist
- Flag/unflag reviews
- Hide/show reviews
- Bulk actions for moderation

## Example Usage

### Creating a Review
```python
from apps.reviews.models import Review

review = Review.objects.create(
    booking=booking,
    client=client_user,
    artist=artist_profile,
    rating=5,
    comment="Amazing work! Very professional."
)
```

### Adding Artist Response
```python
review.add_artist_response("Thank you so much for your kind words!")
```

### Flagging for Moderation
```python
review.flag_for_moderation(reason="Contains spam")
```

### Hiding from Public
```python
review.hide()
```

## Integration Points

- **Bookings App**: Reviews are created for completed bookings
- **Profiles App**: Artist ratings are updated in MakeupArtistProfile
- **Notifications App**: Notifications sent for new reviews and responses
- **Users App**: Client and artist user relationships
