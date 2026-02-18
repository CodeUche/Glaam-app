"""
Tests for the users app: authentication, registration, permissions.
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration endpoint."""

    url = reverse('users:register')

    def test_register_client_success(self, api_client):
        """Test successful client registration."""
        data = {
            'email': 'newclient@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'Client',
            'role': 'client',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['email'] == 'newclient@example.com'
        assert response.data['user']['role'] == 'client'

    def test_register_artist_success(self, api_client):
        """Test successful artist registration."""
        data = {
            'email': 'newartist@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'Artist',
            'role': 'artist',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['role'] == 'artist'

    def test_register_password_mismatch(self, api_client):
        """Test registration fails with mismatched passwords."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'client',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client, client_user):
        """Test registration fails with existing email."""
        data = {
            'email': client_user.email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'client',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        """Test registration fails with weak password."""
        data = {
            'email': 'test@example.com',
            'password': '123',
            'password_confirm': '123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'client',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_admin_role_rejected(self, api_client):
        """Test that users cannot register with admin role."""
        data = {
            'email': 'sneaky@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Sneaky',
            'last_name': 'User',
            'role': 'admin',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Tests for user login endpoint."""

    url = reverse('users:login')

    def test_login_success(self, api_client, client_user):
        """Test successful login returns tokens."""
        data = {
            'email': 'client@example.com',
            'password': 'TestPass123!',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_login_wrong_password(self, api_client, client_user):
        """Test login fails with wrong password."""
        data = {
            'email': 'client@example.com',
            'password': 'WrongPassword!',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login fails for nonexistent user."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!',
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCurrentUser:
    """Tests for current user endpoint."""

    url = reverse('users:current_user')

    def test_get_current_user_authenticated(self, authenticated_client, client_user):
        """Test authenticated user can get their profile."""
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == client_user.email
        assert response.data['role'] == 'client'

    def test_get_current_user_unauthenticated(self, api_client):
        """Test unauthenticated user gets 401."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_current_user(self, authenticated_client):
        """Test updating user profile."""
        data = {'first_name': 'Updated', 'last_name': 'Name'}
        response = authenticated_client.patch(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'


@pytest.mark.django_db
class TestPasswordChange:
    """Tests for password change endpoint."""

    url = reverse('users:password_change')

    def test_change_password_success(self, authenticated_client):
        """Test successful password change."""
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, authenticated_client):
        """Test password change fails with wrong old password."""
        data = {
            'old_password': 'WrongOldPassword!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserModel:
    """Tests for User model methods and properties."""

    def test_user_soft_delete(self, client_user):
        """Test soft delete sets deleted_at and deactivates user."""
        client_user.delete()
        client_user.refresh_from_db()
        assert client_user.deleted_at is not None
        assert client_user.is_active is False

    def test_user_hard_delete(self, create_user):
        """Test hard delete removes user from database."""
        user = create_user(email='disposable@example.com')
        user_id = user.id
        user.delete(soft=False)
        assert not User.objects.filter(id=user_id).exists()

    def test_user_role_properties(self, client_user, artist_user, admin_user):
        """Test role property checks."""
        assert client_user.is_client is True
        assert client_user.is_artist is False
        assert artist_user.is_artist is True
        assert artist_user.is_client is False
        assert admin_user.is_admin_user is True

    def test_user_full_name(self, client_user):
        """Test full_name property."""
        assert client_user.full_name == 'Jane Client'

    def test_profile_created_on_user_creation(self, client_user, artist_user):
        """Test profiles are auto-created via signals."""
        assert hasattr(client_user, 'client_profile')
        assert hasattr(artist_user, 'artist_profile')
