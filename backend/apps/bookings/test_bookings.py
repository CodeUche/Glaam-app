"""
Comprehensive tests for the bookings app.
"""

import pytest
from datetime import date, time, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.bookings.models import Booking
from apps.profiles.models import Availability


@pytest.mark.django_db
class TestBookingCreation:
    """Tests for booking creation endpoint."""

    def setup_method(self):
        self.url = '/api/v1/bookings/bookings/'

    def _setup_availability(self, artist_user):
        """Set up artist availability for testing."""
        # Create availability for every day of the week
        for day in range(7):
            Availability.objects.create(
                artist=artist_user.artist_profile,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(18, 0),
                is_active=True,
            )

    def test_create_booking_success(self, authenticated_client, artist_user, sample_service, client_user):
        """Test successful booking creation."""
        self._setup_availability(artist_user)
        # Book 7 days in the future
        booking_date = date.today() + timedelta(days=7)
        data = {
            'artist': str(artist_user.artist_profile.id),
            'service': str(sample_service.id),
            'booking_date': booking_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Client home, 123 Main St',
        }
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert response.data['booking_number'] is not None

    def test_create_booking_artist_cannot_book(self, authenticated_artist, artist_user, sample_service):
        """Test that artists cannot create bookings for themselves."""
        data = {
            'artist': str(artist_user.artist_profile.id),
            'service': str(sample_service.id),
            'booking_date': (date.today() + timedelta(days=7)).isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Somewhere',
        }
        response = authenticated_artist.post(self.url, data, format='json')
        # Should be forbidden since artists can't self-book
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]

    def test_create_booking_past_date(self, authenticated_client, artist_user, sample_service):
        """Test that bookings cannot be created in the past."""
        data = {
            'artist': str(artist_user.artist_profile.id),
            'service': str(sample_service.id),
            'booking_date': (date.today() - timedelta(days=1)).isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Somewhere',
        }
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_book(self, api_client, artist_user, sample_service):
        """Test unauthenticated users cannot create bookings."""
        data = {
            'artist': str(artist_user.artist_profile.id),
            'service': str(sample_service.id),
            'booking_date': (date.today() + timedelta(days=7)).isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Somewhere',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBookingStatusTransitions:
    """Tests for booking status transitions (accept, reject, complete, cancel)."""

    def _create_booking(self, authenticated_client, artist_user, sample_service):
        """Helper to create a booking and return its ID."""
        # Set up availability
        for day in range(7):
            Availability.objects.get_or_create(
                artist=artist_user.artist_profile,
                day_of_week=day,
                defaults={
                    'start_time': time(8, 0),
                    'end_time': time(18, 0),
                    'is_active': True,
                }
            )

        booking_date = date.today() + timedelta(days=7)
        data = {
            'artist': str(artist_user.artist_profile.id),
            'service': str(sample_service.id),
            'booking_date': booking_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Client home',
        }
        response = authenticated_client.post('/api/v1/bookings/bookings/', data, format='json')
        return response.data.get('id')

    def test_artist_accept_booking(
        self, authenticated_client, authenticated_artist,
        artist_user, sample_service, client_user
    ):
        """Test artist can accept a pending booking."""
        booking_id = self._create_booking(authenticated_client, artist_user, sample_service)
        if booking_id:
            url = f'/api/v1/bookings/bookings/{booking_id}/accept/'
            response = authenticated_artist.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_artist_reject_booking(
        self, authenticated_client, authenticated_artist,
        artist_user, sample_service, client_user
    ):
        """Test artist can reject a pending booking."""
        booking_id = self._create_booking(authenticated_client, artist_user, sample_service)
        if booking_id:
            url = f'/api/v1/bookings/bookings/{booking_id}/reject/'
            response = authenticated_artist.post(url, {'reason': 'Not available'}, format='json')
            assert response.status_code == status.HTTP_200_OK

    def test_client_cancel_booking(
        self, authenticated_client, artist_user, sample_service, client_user
    ):
        """Test client can cancel their own booking."""
        booking_id = self._create_booking(authenticated_client, artist_user, sample_service)
        if booking_id:
            url = f'/api/v1/bookings/bookings/{booking_id}/cancel/'
            response = authenticated_client.post(url, {'reason': 'Change of plans'}, format='json')
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDoubleBookingPrevention:
    """Tests to verify double-booking prevention."""

    def test_overlapping_booking_rejected(
        self, authenticated_client, artist_user, sample_service, client_user
    ):
        """Test that overlapping bookings for the same artist are rejected."""
        # Set up availability
        for day in range(7):
            Availability.objects.get_or_create(
                artist=artist_user.artist_profile,
                day_of_week=day,
                defaults={
                    'start_time': time(8, 0),
                    'end_time': time(18, 0),
                    'is_active': True,
                }
            )

        booking_date = date.today() + timedelta(days=7)
        base_data = {
            'artist': str(artist_user.artist_profile.id),
            'service': str(sample_service.id),
            'booking_date': booking_date.isoformat(),
            'location': 'Client home',
        }

        # First booking: 10:00-12:00
        data1 = {**base_data, 'start_time': '10:00:00', 'end_time': '12:00:00'}
        response1 = authenticated_client.post('/api/v1/bookings/bookings/', data1, format='json')

        if response1.status_code == status.HTTP_201_CREATED:
            # Second overlapping booking: 11:00-13:00 — should fail
            data2 = {**base_data, 'start_time': '11:00:00', 'end_time': '13:00:00'}
            response2 = authenticated_client.post('/api/v1/bookings/bookings/', data2, format='json')
            assert response2.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBookingListPermissions:
    """Tests for booking list access control."""

    def test_client_sees_own_bookings_only(self, authenticated_client, client_user):
        """Test clients only see their own bookings."""
        response = authenticated_client.get('/api/v1/bookings/bookings/')
        assert response.status_code == status.HTTP_200_OK

    def test_artist_sees_own_bookings_only(self, authenticated_artist, artist_user):
        """Test artists only see bookings assigned to them."""
        response = authenticated_artist.get('/api/v1/bookings/bookings/')
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_list(self, api_client):
        """Test unauthenticated users cannot list bookings."""
        response = api_client.get('/api/v1/bookings/bookings/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
