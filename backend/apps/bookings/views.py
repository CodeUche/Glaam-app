"""
Views for bookings app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Booking, BookingStatus
from apps.services.models import Service
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingStatusUpdateSerializer,
    ServiceSerializer,
    AvailabilityCheckSerializer,
)
from .permissions import (
    IsClient,
    IsArtist,
    IsBookingParticipant,
    IsBookingArtist,
    IsServiceOwner,
)
from .utils import check_artist_availability, get_available_time_slots
from apps.profiles.models import MakeupArtistProfile


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing services.

    Artists can create, update, and delete their own services.
    Anyone can view active services.
    """

    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['artist', 'category', 'is_active']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['price', 'duration', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create']:
            return [IsAuthenticated(), IsArtist()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsServiceOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role."""
        queryset = super().get_queryset()
        user = self.request.user

        # Artists can see all their services (including inactive)
        if user.role == 'artist' and hasattr(user, 'artist_profile'):
            return Service.objects.filter(artist=user.artist_profile)

        # Others can only see active services
        return queryset.filter(is_active=True)

    def perform_destroy(self, instance):
        """Soft delete by marking as inactive."""
        instance.is_active = False
        instance.save()


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.

    Clients can create and view their bookings.
    Artists can view their bookings and update status.
    """

    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'booking_date', 'artist', 'service']
    search_fields = ['booking_number', 'location']
    ordering_fields = ['booking_date', 'created_at', 'start_time']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        return BookingDetailSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            return [IsAuthenticated(), IsClient()]
        elif self.action in ['accept', 'reject', 'complete']:
            return [IsAuthenticated(), IsArtist(), IsBookingArtist()]
        elif self.action in ['retrieve', 'list']:
            return [IsAuthenticated()]
        elif self.action == 'cancel':
            return [IsAuthenticated(), IsBookingParticipant()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter bookings based on user role."""
        user = self.request.user
        queryset = super().get_queryset()

        # Clients see their own bookings
        if user.role == 'client':
            return queryset.filter(client=user)

        # Artists see bookings for them
        elif user.role == 'artist' and hasattr(user, 'artist_profile'):
            return queryset.filter(artist=user.artist_profile)

        # Admins see all bookings
        elif user.role == 'admin' or user.is_superuser:
            return queryset

        return queryset.none()

    def perform_create(self, serializer):
        """Create booking and send notification."""
        booking = serializer.save()

        # Send notification to artist (async)
        from .tasks import send_booking_notification
        send_booking_notification.delay(
            booking_id=str(booking.id),
            notification_type='new_booking'
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsArtist])
    def accept(self, request, pk=None):
        """Accept a booking (artist only)."""
        booking = self.get_object()

        # Check permission
        if not hasattr(request.user, 'artist_profile') or booking.artist != request.user.artist_profile:
            return Response(
                {'detail': 'You do not have permission to accept this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and accept
        serializer = BookingStatusUpdateSerializer(
            data=request.data,
            context={'booking': booking, 'action': 'accept'}
        )
        serializer.is_valid(raise_exception=True)

        try:
            booking.accept()

            # Send notification to client (async)
            from .tasks import send_booking_notification
            send_booking_notification.delay(
                booking_id=str(booking.id),
                notification_type='booking_accepted'
            )

            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except DjangoValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsArtist])
    def reject(self, request, pk=None):
        """Reject a booking (artist only)."""
        booking = self.get_object()

        # Check permission
        if not hasattr(request.user, 'artist_profile') or booking.artist != request.user.artist_profile:
            return Response(
                {'detail': 'You do not have permission to reject this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and reject
        serializer = BookingStatusUpdateSerializer(
            data=request.data,
            context={'booking': booking, 'action': 'reject'}
        )
        serializer.is_valid(raise_exception=True)

        try:
            reason = serializer.validated_data.get('reason')
            booking.reject(reason=reason)

            # Send notification to client (async)
            from .tasks import send_booking_notification
            send_booking_notification.delay(
                booking_id=str(booking.id),
                notification_type='booking_rejected'
            )

            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except DjangoValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsArtist])
    def complete(self, request, pk=None):
        """Mark booking as completed (artist only)."""
        booking = self.get_object()

        # Check permission
        if not hasattr(request.user, 'artist_profile') or booking.artist != request.user.artist_profile:
            return Response(
                {'detail': 'You do not have permission to complete this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and complete
        serializer = BookingStatusUpdateSerializer(
            data=request.data,
            context={'booking': booking, 'action': 'complete'}
        )
        serializer.is_valid(raise_exception=True)

        try:
            booking.complete()

            # Send notification to client (async)
            from .tasks import send_booking_notification
            send_booking_notification.delay(
                booking_id=str(booking.id),
                notification_type='booking_completed'
            )

            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except DjangoValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()

        # Check permission - must be client or artist
        is_client = booking.client == request.user
        is_artist = (
            hasattr(request.user, 'artist_profile') and
            booking.artist == request.user.artist_profile
        )

        if not (is_client or is_artist):
            return Response(
                {'detail': 'You do not have permission to cancel this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and cancel
        serializer = BookingStatusUpdateSerializer(
            data=request.data,
            context={'booking': booking, 'action': 'cancel'}
        )
        serializer.is_valid(raise_exception=True)

        try:
            cancelled_by = 'client' if is_client else 'artist'
            reason = serializer.validated_data.get('reason')
            booking.cancel(cancelled_by=cancelled_by, reason=reason)

            # Send notification to the other party (async)
            from .tasks import send_booking_notification
            send_booking_notification.delay(
                booking_id=str(booking.id),
                notification_type='booking_cancelled'
            )

            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except DjangoValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def check_availability(self, request):
        """
        Check artist availability for a specific date and time.

        Request body:
        {
            "artist_id": "uuid",
            "booking_date": "2026-03-15",
            "start_time": "10:00:00",
            "end_time": "12:00:00"
        }
        """
        serializer = AvailabilityCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artist = serializer.validated_data['artist']
        booking_date = serializer.validated_data['booking_date']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']

        try:
            is_available = check_artist_availability(
                artist=artist,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time
            )

            return Response({
                'available': is_available,
                'artist_id': str(artist.id),
                'artist_name': artist.user.full_name,
                'booking_date': booking_date,
                'start_time': start_time,
                'end_time': end_time,
            }, status=status.HTTP_200_OK)

        except DjangoValidationError as e:
            return Response({
                'available': False,
                'reason': str(e),
                'artist_id': str(artist.id),
                'booking_date': booking_date,
                'start_time': start_time,
                'end_time': end_time,
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def available_slots(self, request):
        """
        Get available time slots for an artist on a specific date.

        Query params:
        - artist_id: UUID of the artist
        - booking_date: Date (YYYY-MM-DD)
        - duration_minutes: Duration of the service (default: 60)
        """
        artist_id = request.query_params.get('artist_id')
        booking_date_str = request.query_params.get('booking_date')
        duration_minutes = int(request.query_params.get('duration_minutes', 60))

        if not artist_id or not booking_date_str:
            return Response(
                {'detail': 'artist_id and booking_date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            artist = MakeupArtistProfile.objects.get(id=artist_id)
        except MakeupArtistProfile.DoesNotExist:
            return Response(
                {'detail': 'Artist not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            from datetime import datetime
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get available slots
        slots = get_available_time_slots(artist, booking_date, duration_minutes)

        return Response({
            'artist_id': str(artist.id),
            'artist_name': artist.user.full_name,
            'booking_date': booking_date,
            'duration_minutes': duration_minutes,
            'available_slots': [
                {
                    'start_time': start_time.strftime('%H:%M'),
                    'end_time': end_time.strftime('%H:%M')
                }
                for start_time, end_time in slots
            ],
            'total_slots': len(slots)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def statistics(self, request):
        """
        Get booking statistics for the current user.

        For clients: returns their booking stats
        For artists: returns their booking stats
        """
        from .utils import get_booking_statistics

        user = request.user

        if user.role == 'client':
            stats = get_booking_statistics(client=user)
        elif user.role == 'artist' and hasattr(user, 'artist_profile'):
            stats = get_booking_statistics(artist=user.artist_profile)
        else:
            stats = {}

        return Response(stats, status=status.HTTP_200_OK)
