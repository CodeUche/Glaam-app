"""
Permissions for the notifications app.
"""

from rest_framework import permissions


class IsNotificationOwner(permissions.BasePermission):
    """
    Permission to only allow owners of a notification to access it.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user owns the notification.
        """
        return obj.user == request.user
