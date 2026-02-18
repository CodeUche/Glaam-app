# Permissions Reference - Profiles App

## Custom Permission Classes

### IsOwnerOrReadOnly
**Location**: `apps/profiles/views.py`

**Description**: Allows read access to authenticated users, write access only to owners.

**Implementation**:
```python
class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
```

**Used By**:
- Client profiles
- Artist profiles

### IsArtist
**Location**: `apps/profiles/views.py`

**Description**: Ensures the authenticated user has the 'artist' role.

**Implementation**:
```python
class IsArtist(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == 'artist'
```

**Used By**:
- Portfolio image management
- Availability management
- Availability exception management

## ViewSet Permissions Matrix

### ClientProfileViewSet

| Action | Permission | Notes |
|--------|-----------|-------|
| list | IsAuthenticated | Staff can see all, users see own |
| retrieve | IsAuthenticated | Users can only see own profile |
| create | Automatic | Created on user registration |
| update | IsAuthenticated | Users can only update own profile |
| partial_update | IsAuthenticated | Users can only update own profile |
| destroy | IsAuthenticated + Admin | Only admins can delete |
| me | IsAuthenticated | Special endpoint for current user |

### MakeupArtistProfileViewSet

| Action | Permission | Notes |
|--------|-----------|-------|
| list | AllowAny | Public listing with filtering |
| retrieve | AllowAny | Public artist profiles |
| create | IsArtist | Only users with artist role |
| update | IsArtist + Owner | Artist can only update own profile |
| partial_update | IsArtist + Owner | Artist can only update own profile |
| destroy | IsArtist + Owner | Artist can delete own profile |
| me | IsAuthenticated + Artist | Special endpoint for current artist |
| portfolio | AllowAny | Public endpoint to view artist's portfolio |
| availability | AllowAny | Public endpoint to view artist's schedule |
| toggle_favorite | IsAuthenticated | Any authenticated user can favorite |

### PortfolioImageViewSet

| Action | Permission | Notes |
|--------|-----------|-------|
| list | AllowAny | Public portfolio viewing |
| retrieve | AllowAny | Public image viewing |
| create | IsArtist | Only artists can upload images |
| update | IsArtist + Owner | Artist can only update own images |
| partial_update | IsArtist + Owner | Artist can only update own images |
| destroy | IsArtist + Owner | Artist can only delete own images |
| my_portfolio | IsArtist | List current artist's portfolio |
| toggle_featured | IsArtist + Owner | Toggle featured status |
| reorder | IsArtist | Reorder own portfolio images |

### FavoriteViewSet

| Action | Permission | Notes |
|--------|-----------|-------|
| list | IsAuthenticated | User sees only their favorites |
| retrieve | IsAuthenticated | User can view their favorites |
| create | IsAuthenticated | Add artist to favorites |
| destroy | IsAuthenticated + Owner | User can only delete own favorites |
| my_favorites | IsAuthenticated | Special endpoint for user's favorites |

### AvailabilityViewSet

| Action | Permission | Notes |
|--------|-----------|-------|
| list | AllowAny | Public viewing of schedules |
| retrieve | AllowAny | Public viewing of specific slot |
| create | IsArtist | Artist sets own availability |
| update | IsArtist + Owner | Artist updates own availability |
| partial_update | IsArtist + Owner | Artist updates own availability |
| destroy | IsArtist + Owner | Artist removes availability slot |
| my_schedule | IsArtist | View current artist's full schedule |

### AvailabilityExceptionViewSet

| Action | Permission | Notes |
|--------|-----------|-------|
| list | AllowAny | Public viewing of exceptions |
| retrieve | AllowAny | Public viewing of specific exception |
| create | IsArtist | Artist creates exceptions |
| update | IsArtist + Owner | Artist updates own exceptions |
| partial_update | IsArtist + Owner | Artist updates own exceptions |
| destroy | IsArtist + Owner | Artist removes exceptions |
| my_exceptions | IsArtist | View current artist's exceptions |

## Serializer-Level Validation

### Ownership Validation

**ClientProfileSerializer**:
- Validates that user can only update their own profile
- Notification preferences structure validation

**MakeupArtistProfileWriteSerializer**:
- Validates specialties are from allowed choices
- Validates experience range (0-50 years)
- Validates hourly rate is positive and reasonable
- Validates coordinate ranges for latitude/longitude

**PortfolioImageSerializer**:
- Validates artist ownership on create/update
- Automatically sets artist from authenticated user
- Prevents non-artists from uploading
- Validates display order is non-negative

**FavoriteSerializer**:
- Prevents duplicate favorites
- Prevents self-favoriting (artist favoriting their own profile)
- Automatically sets client from authenticated user

**AvailabilitySerializer**:
- Validates time ranges (start before end)
- Validates day of week (0-6)
- Prevents overlapping time slots
- Validates artist ownership
- Automatically sets artist from authenticated user

**AvailabilityExceptionSerializer**:
- Validates date is not in the past
- Validates time ranges when marked as available
- Validates artist ownership
- Automatically sets artist from authenticated user

## Admin Permissions

All admin functionality requires:
1. User must be authenticated
2. User must have `is_staff=True`
3. User must have appropriate model permissions

### Custom Admin Actions

**MakeupArtistProfileAdmin**:
- `verify_artists`: Requires change permission
- `unverify_artists`: Requires change permission
- `mark_available`: Requires change permission
- `mark_unavailable`: Requires change permission

**PortfolioImageAdmin**:
- `mark_featured`: Requires change permission
- `unmark_featured`: Requires change permission

**AvailabilityAdmin**:
- `activate_availability`: Requires change permission
- `deactivate_availability`: Requires change permission

## Security Checks

### Authentication Checks
```python
# Check if user is authenticated
if not request.user.is_authenticated:
    return Response(status=401)
```

### Role Checks
```python
# Check if user is an artist
if request.user.role != 'artist':
    raise PermissionDenied()
```

### Ownership Checks
```python
# Check if user owns the resource
if obj.user != request.user:
    raise PermissionDenied()

# For nested resources (e.g., portfolio images)
if obj.artist.user != request.user:
    raise PermissionDenied()
```

### Profile Existence Checks
```python
# Check if artist profile exists
try:
    artist_profile = request.user.artist_profile
except MakeupArtistProfile.DoesNotExist:
    raise ValidationError("Artist profile not found.")
```

## Common Permission Patterns

### Read: Public, Write: Owner
Used for artist profiles and portfolio images:
```python
def get_permissions(self):
    if self.action in ['list', 'retrieve']:
        return [AllowAny()]
    return [IsArtist()]
```

### All Operations: Authenticated + Owner
Used for favorites and client profiles:
```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    return Model.objects.filter(user=self.request.user)
```

### Create: Role-Based, Update: Owner
Used for artist-specific resources:
```python
def get_permissions(self):
    if self.action in ['create', 'update', 'destroy']:
        return [IsArtist()]
    return super().get_permissions()
```

## Permission Error Responses

### 401 Unauthorized
**When**: User is not authenticated
**Response**:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
**When**: User is authenticated but lacks permission
**Response**:
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### Custom Permission Messages
**Example**:
```json
{
    "error": "Only makeup artists can upload portfolio images."
}
```

## Testing Permissions

### Test Unauthenticated Access
```python
def test_requires_authentication(self):
    response = self.client.get('/api/profiles/favorites/')
    self.assertEqual(response.status_code, 401)
```

### Test Role-Based Access
```python
def test_requires_artist_role(self):
    self.client.force_authenticate(user=self.client_user)
    response = self.client.post('/api/profiles/portfolio/', data)
    self.assertEqual(response.status_code, 403)
```

### Test Ownership
```python
def test_owner_can_update(self):
    self.client.force_authenticate(user=self.owner)
    response = self.client.put(url, data)
    self.assertEqual(response.status_code, 200)

def test_non_owner_cannot_update(self):
    self.client.force_authenticate(user=self.other_user)
    response = self.client.put(url, data)
    self.assertEqual(response.status_code, 403)
```

## Best Practices

1. **Always authenticate for write operations**: Never allow unauthenticated writes
2. **Verify ownership**: Always check if the user owns the resource they're modifying
3. **Use role-based permissions**: Separate client and artist capabilities
4. **Validate in serializers**: Add validation logic in serializers, not just views
5. **Fail securely**: Default to denying access if unsure
6. **Log permission failures**: Track unauthorized access attempts
7. **Use DRF permission classes**: Leverage built-in permission system
8. **Test edge cases**: Test permissions for all user types and scenarios

## Quick Reference

| Resource | Create | Read | Update | Delete |
|----------|--------|------|--------|--------|
| Client Profile | Auto | Owner | Owner | Admin |
| Artist Profile | Artist | Public | Owner | Owner |
| Portfolio Image | Artist | Public | Owner | Owner |
| Favorite | Auth | Owner | - | Owner |
| Availability | Artist | Public | Owner | Owner |
| Availability Exception | Artist | Public | Owner | Owner |

**Legend**:
- Auto: Automatically created
- Owner: Resource owner only
- Artist: Users with artist role
- Auth: Any authenticated user
- Public: Anyone (including unauthenticated)
- Admin: Staff/admin users only
