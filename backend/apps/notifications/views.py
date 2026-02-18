"""
Views for the notifications app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import CursorPagination
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    MarkAsReadSerializer,
    NotificationStatsSerializer,
)


class NotificationPagination(CursorPagination):
    """Custom pagination for notifications."""
    page_size = 20
    ordering = '-created_at'
    cursor_query_param = 'cursor'


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for notifications.

    Provides:
    - List notifications (GET /api/v1/notifications/)
    - Retrieve notification (GET /api/v1/notifications/:id/)
    - Mark as read (PATCH /api/v1/notifications/:id/mark-read/)
    - Mark all as read (POST /api/v1/notifications/mark-all-read/)
    - Bulk mark as read (POST /api/v1/notifications/bulk-mark-read/)
    - Delete notification (DELETE /api/v1/notifications/:id/)
    - Get statistics (GET /api/v1/notifications/stats/)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        """Get notifications for the current user."""
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_read=is_read_bool)

        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by related booking
        booking_id = self.request.query_params.get('booking_id')
        if booking_id:
            queryset = queryset.filter(related_booking_id=booking_id)

        return queryset.select_related('user', 'related_booking')

    def get_serializer_class(self):
        """Get appropriate serializer class."""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    def list(self, request, *args, **kwargs):
        """List notifications with unread count."""
        response = super().list(request, *args, **kwargs)

        # Add unread count to response
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        response.data['unread_count'] = unread_count
        return response

    @action(detail=True, methods=['patch'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()

        if notification.is_read:
            return Response(
                {'detail': 'Notification already marked as read.'},
                status=status.HTTP_200_OK
            )

        notification.mark_as_read()

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user."""
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            'detail': f'Marked {updated_count} notification(s) as read.',
            'count': updated_count
        })

    @action(detail=False, methods=['post'], url_path='bulk-mark-read')
    def bulk_mark_read(self, request):
        """Mark multiple notifications as read."""
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids')

        if notification_ids:
            # Mark specific notifications as read
            updated_count = Notification.objects.filter(
                user=request.user,
                id__in=notification_ids,
                is_read=False
            ).update(is_read=True)
        else:
            # Mark all as read if no IDs provided
            updated_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True)

        return Response({
            'detail': f'Marked {updated_count} notification(s) as read.',
            'count': updated_count
        })

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get notification statistics for the current user."""
        notifications = Notification.objects.filter(user=request.user)

        total = notifications.count()
        unread = notifications.filter(is_read=False).count()
        read = notifications.filter(is_read=True).count()

        # Count by type
        by_type = dict(
            notifications.values('notification_type')
            .annotate(count=Count('id'))
            .values_list('notification_type', 'count')
        )

        stats_data = {
            'total': total,
            'unread': unread,
            'read': read,
            'by_type': by_type,
        }

        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a notification."""
        notification = self.get_object()
        notification.delete()

        return Response(
            {'detail': 'Notification deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_all(self, request):
        """Delete all notifications for the current user."""
        deleted_count, _ = Notification.objects.filter(user=request.user).delete()

        return Response({
            'detail': f'Deleted {deleted_count} notification(s).',
            'count': deleted_count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='clear-read')
    def clear_read(self, request):
        """Delete all read notifications for the current user."""
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()

        return Response({
            'detail': f'Deleted {deleted_count} read notification(s).',
            'count': deleted_count
        }, status=status.HTTP_200_OK)
