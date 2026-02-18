"""
Custom permissions for services app.
"""

from rest_framework import permissions


class IsArtistOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow artist owners to edit/delete their services.
    Read-only access for everyone else.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions require authenticated artist
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'artist_profile')
            and request.user.is_artist
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the artist owner
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'artist_profile'):
            return False

        return obj.artist == request.user.artist_profile


class IsArtistOwner(permissions.BasePermission):
    """
    Permission to only allow artist owners to perform actions on their services.
    No read-only access - requires ownership.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'artist_profile')
            and request.user.is_artist
        )

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'artist_profile'):
            return False

        return obj.artist == request.user.artist_profile
