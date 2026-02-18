"""
Custom permissions for user app.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj == request.user


class IsClient(permissions.BasePermission):
    """
    Permission to only allow clients.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_client


class IsArtist(permissions.BasePermission):
    """
    Permission to only allow makeup artists.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_artist


class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user


class IsClientOrArtist(permissions.BasePermission):
    """
    Permission to allow either clients or artists.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_client or request.user.is_artist)
        )
