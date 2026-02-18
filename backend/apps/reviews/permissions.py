"""
Custom permissions for reviews app.
"""

from rest_framework import permissions


class IsClient(permissions.BasePermission):
    """
    Permission to check if user is a client.
    Only clients can create reviews.
    """

    message = "Only clients can create reviews."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )


class IsArtist(permissions.BasePermission):
    """
    Permission to check if user is an artist.
    Only artists can respond to reviews.
    """

    message = "Only artists can respond to reviews."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )


class IsReviewClient(permissions.BasePermission):
    """
    Permission to check if user is the client who wrote the review.
    Clients can view their own reviews.
    """

    message = "You don't have permission to access this review."

    def has_object_permission(self, request, view, obj):
        return obj.client == request.user


class IsReviewArtist(permissions.BasePermission):
    """
    Permission to check if user is the artist being reviewed.
    Artists can respond to reviews about them.
    """

    message = "You can only respond to reviews about you."

    def has_object_permission(self, request, view, obj):
        return (
            hasattr(request.user, 'artist_profile') and
            obj.artist == request.user.artist_profile
        )


class CanViewReview(permissions.BasePermission):
    """
    Permission to check if user can view a review.
    - Public reviews can be viewed by anyone
    - Hidden reviews can only be viewed by client, artist, or admin
    """

    message = "This review is not publicly visible."

    def has_object_permission(self, request, view, obj):
        # If review is visible, anyone can see it
        if obj.is_visible:
            return True

        # If not visible, check if user is involved or admin
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin can view any review
        if request.user.is_admin_user:
            return True

        # Client who wrote the review can view it
        if obj.client == request.user:
            return True

        # Artist being reviewed can view it
        if hasattr(request.user, 'artist_profile') and obj.artist == request.user.artist_profile:
            return True

        return False


class CanModerateReview(permissions.BasePermission):
    """
    Permission for admin moderation actions.
    Only admins can flag, hide, or moderate reviews.
    """

    message = "Only administrators can moderate reviews."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin_user or request.user.is_staff)
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin_user or request.user.is_staff)
        )


class CanCreateReview(permissions.BasePermission):
    """
    Complex permission to check if user can create a review.
    User must be a client with a completed booking.
    """

    message = "You can only review bookings you've completed."

    def has_permission(self, request, view):
        # Must be authenticated client
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.role != 'client':
            self.message = "Only clients can create reviews."
            return False

        return True


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admin can do anything, others can only read.
    """

    def has_permission(self, request, view):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for admin
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin_user or request.user.is_staff)
        )
