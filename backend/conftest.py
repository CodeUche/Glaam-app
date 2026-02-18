"""
Shared test fixtures for GlamConnect backend.
"""

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.profiles.models import MakeupArtistProfile, ClientProfile
from apps.services.models import Service

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def create_user():
    """Factory fixture to create users."""
    def _create_user(
        email='testuser@example.com',
        password='TestPass123!',
        role='client',
        first_name='Test',
        last_name='User',
        **kwargs
    ):
        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        return user
    return _create_user


@pytest.fixture
def client_user(create_user):
    """Create a client user with profile."""
    user = create_user(
        email='client@example.com',
        role='client',
        first_name='Jane',
        last_name='Client'
    )
    # Profile created via signal
    return user


@pytest.fixture
def artist_user(create_user):
    """Create an artist user with profile."""
    user = create_user(
        email='artist@example.com',
        role='artist',
        first_name='Maria',
        last_name='Artist'
    )
    # Ensure artist profile exists and has required fields
    profile = user.artist_profile
    profile.bio = 'Professional makeup artist with 5 years experience.'
    profile.location = 'New York, NY'
    profile.hourly_rate = 75.00
    profile.specialties = ['bridal', 'editorial']
    profile.years_of_experience = 5
    profile.is_available = True
    profile.save()
    return user


@pytest.fixture
def admin_user(create_user):
    """Create an admin user."""
    user = create_user(
        email='admin@example.com',
        role='admin',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def authenticated_client(api_client, client_user):
    """Return an API client authenticated as a client user."""
    refresh = RefreshToken.for_user(client_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def authenticated_artist(api_client, artist_user):
    """Return an API client authenticated as an artist user."""
    refresh = RefreshToken.for_user(artist_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def authenticated_admin(api_client, admin_user):
    """Return an API client authenticated as an admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def sample_service(artist_user):
    """Create a sample service for an artist."""
    return Service.objects.create(
        artist=artist_user.artist_profile,
        name='Bridal Makeup Package',
        description='Full bridal makeup with trial session included.',
        category='bridal',
        price=250.00,
        duration=120,
        is_active=True,
    )


@pytest.fixture
def sample_services(artist_user):
    """Create multiple sample services for an artist."""
    services = []
    data = [
        ('Bridal Makeup', 'Complete bridal package.', 'bridal', 250.00, 120),
        ('Natural Everyday', 'Light, natural look.', 'natural', 75.00, 45),
        ('Glam Night Out', 'Full glam for events.', 'glam', 150.00, 90),
    ]
    for name, desc, cat, price, dur in data:
        services.append(Service.objects.create(
            artist=artist_user.artist_profile,
            name=name,
            description=desc,
            category=cat,
            price=price,
            duration=dur,
            is_active=True,
        ))
    return services
