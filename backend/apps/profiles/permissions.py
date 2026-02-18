"""
Custom permissions for profiles app.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a profile to edit it.
    Read permissions are allowed to any authenticated user.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsArtist(permissions.BasePermission):
    """
    Permission class to ensure user is a makeup artist.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )


class IsClient(permissions.BasePermission):
    """
    Permission class to ensure user is a client.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )


class IsArtistOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow artist owners to edit their content.
    Read permissions are allowed to anyone.
    """

    def has_permission(self, request, view):
        # Allow read permissions for all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions require authentication and artist role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the artist owner
        if hasattr(obj, 'artist'):
            return obj.artist.user == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsClientOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow clients to create/edit favorites.
    Read permissions are allowed to authenticated users.
    """

    def has_permission(self, request, view):
        # Allow read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions require authentication and client role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to the client owner
        if hasattr(obj, 'client'):
            return obj.client == request.user
        return False


class IsProfileOwner(permissions.BasePermission):
    """
    Permission to only allow users to access their own profile.
    """

    def has_object_permission(self, request, view, obj):
        # Profile owner check
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsStaffOrOwner(permissions.BasePermission):
    """
    Custom permission to allow staff to manage all resources,
    and regular users to only manage their own.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True

        # Check ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'artist'):
            return obj.artist.user == request.user
        elif hasattr(obj, 'client'):
            return obj.client == request.user
        return False


class CanManageAvailability(permissions.BasePermission):
    """
    Permission to allow only artists to manage their availability.
    """

    def has_permission(self, request, view):
        # Allow read permissions for all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions require authentication and artist role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the artist owner
        if hasattr(obj, 'artist'):
            return obj.artist.user == request.user
        return False


class CanManagePortfolio(permissions.BasePermission):
    """
    Permission to allow only artists to manage their portfolio images.
    """

    def has_permission(self, request, view):
        # Allow read permissions for all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions require authentication and artist role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the artist owner
        if hasattr(obj, 'artist'):
            return obj.artist.user == request.user
        return False
