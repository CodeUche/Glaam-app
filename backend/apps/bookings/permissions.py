"""
Custom permissions for bookings app.
"""

from rest_framework import permissions


class IsClient(permissions.BasePermission):
    """
    Permission to check if user is a client.
    """

    message = "Only clients can perform this action."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'client'


class IsArtist(permissions.BasePermission):
    """
    Permission to check if user is an artist.
    """

    message = "Only artists can perform this action."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'artist'


class IsBookingClient(permissions.BasePermission):
    """
    Permission to check if user is the client of the booking.
    """

    message = "You don't have permission to access this booking."

    def has_object_permission(self, request, view, obj):
        return obj.client == request.user


class IsBookingArtist(permissions.BasePermission):
    """
    Permission to check if user is the artist of the booking.
    """

    message = "You don't have permission to access this booking."

    def has_object_permission(self, request, view, obj):
        return (
            hasattr(request.user, 'artist_profile') and
            obj.artist == request.user.artist_profile
        )


class IsBookingParticipant(permissions.BasePermission):
    """
    Permission to check if user is either the client or artist of the booking.
    """

    message = "You don't have permission to access this booking."

    def has_object_permission(self, request, view, obj):
        # Check if user is the client
        if obj.client == request.user:
            return True

        # Check if user is the artist
        if hasattr(request.user, 'artist_profile') and obj.artist == request.user.artist_profile:
            return True

        return False


class IsServiceOwner(permissions.BasePermission):
    """
    Permission to check if user is the owner of the service (artist).
    """

    message = "You don't have permission to modify this service."

    def has_object_permission(self, request, view, obj):
        return (
            hasattr(request.user, 'artist_profile') and
            obj.artist == request.user.artist_profile
        )
