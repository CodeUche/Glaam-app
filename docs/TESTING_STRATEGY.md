# GlamConnect Testing Strategy

## Overview

GlamConnect uses a layered testing approach: unit tests, API integration tests, and frontend component tests. All tests run via `pytest` for the backend and `jest`/`react-testing-library` for the frontend.

---

## Backend Testing

### Setup
```bash
cd backend
pip install -r requirements.txt
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=apps               # With coverage report
pytest -m "not slow"            # Skip slow tests
pytest apps/bookings/           # Run specific app tests
```

### Test Categories

#### 1. Model Tests
- Field validation and constraints
- Custom model methods
- Soft delete behavior
- Signal handlers
- Property calculations

#### 2. Serializer Tests
- Input validation
- Password matching
- Role restrictions
- Required field enforcement
- Nested serializer behavior

#### 3. API Integration Tests
- Full request/response cycle
- Authentication required
- Permission enforcement
- Status code verification
- Response data structure

#### 4. Permission Tests
- Role-based access (client, artist, admin)
- Object-level permissions (only owner can edit)
- Unauthenticated access blocked
- Cross-role access prevention

#### 5. Booking Edge Cases
- Double-booking prevention
- Past date rejection
- Overlapping time slots
- Status transition validation
- Cancellation policy enforcement
- Availability checking

#### 6. Review Validation
- One review per booking
- Completed booking requirement
- Rating range (1-5)
- Spam detection
- Artist response permissions

### Test Fixtures (conftest.py)
- `api_client` — Unauthenticated REST client
- `client_user` — Client user with profile
- `artist_user` — Artist user with complete profile
- `admin_user` — Admin/superuser
- `authenticated_client` — JWT-authenticated client
- `authenticated_artist` — JWT-authenticated artist
- `sample_service` — Artist service fixture
- `sample_services` — Multiple services

---

## Frontend Testing

### Web (Next.js)
```bash
cd frontend/web
npm run test                    # Run all tests
npm run test -- --coverage      # With coverage
```

### Test Categories

#### Component Tests
- UI components render correctly
- Form validation works
- User interactions trigger correct callbacks
- Loading and error states display

#### Integration Tests
- API calls made with correct parameters
- Auth state management
- Navigation flows
- Form submission and error handling

#### Key Scenarios
- Login/registration flow
- Artist search and filtering
- Booking creation flow
- Review submission
- Real-time notification display

---

## Test Coverage Targets

| Area | Target |
|------|--------|
| Models | 90%+ |
| Serializers | 85%+ |
| Views/APIs | 80%+ |
| Permissions | 95%+ |
| Booking logic | 95%+ |
| Frontend components | 70%+ |

---

## CI/CD Integration

Tests should run on every pull request. Suggested GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_glamconnect
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest --cov=apps
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_glamconnect
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
          DEBUG: True

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: cd frontend/web && npm ci && npm test
```
