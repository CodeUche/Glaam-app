"""
Utility functions for bookings app.
"""

from datetime import datetime, time, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Booking, BookingStatus
from apps.profiles.models import Availability, AvailabilityException


def check_artist_availability(artist, booking_date, start_time, end_time, exclude_booking_id=None):
    """
    Check if an artist is available for a given date and time slot.

    Args:
        artist: MakeupArtistProfile instance
        booking_date: date object
        start_time: time object
        end_time: time object
        exclude_booking_id: UUID of booking to exclude (for updates)

    Returns:
        bool: True if available, False otherwise

    Raises:
        ValidationError: If validation fails
    """
    # Check if artist is generally available
    if not artist.is_available:
        raise ValidationError("This artist is not currently accepting bookings.")

    # Check for availability exceptions on this date
    exception = AvailabilityException.objects.filter(
        artist=artist,
        date=booking_date
    ).first()

    if exception:
        # If there's an exception marking the day as unavailable
        if not exception.is_available:
            raise ValidationError(
                f"Artist is not available on {booking_date.strftime('%Y-%m-%d')}. "
                f"Reason: {exception.reason or 'Day blocked'}"
            )

        # If there's a special availability window, check if time fits
        if exception.start_time and exception.end_time:
            if not (exception.start_time <= start_time and end_time <= exception.end_time):
                raise ValidationError(
                    f"Artist is only available from {exception.start_time.strftime('%H:%M')} "
                    f"to {exception.end_time.strftime('%H:%M')} on this date."
                )
    else:
        # Check regular weekly availability
        day_of_week = booking_date.weekday()
        regular_availability = Availability.objects.filter(
            artist=artist,
            day_of_week=day_of_week,
            is_active=True
        )

        if not regular_availability.exists():
            raise ValidationError(
                f"Artist is not available on {booking_date.strftime('%A')}s."
            )

        # Check if requested time falls within any availability window
        time_fits = False
        for availability in regular_availability:
            if availability.start_time <= start_time and end_time <= availability.end_time:
                time_fits = True
                break

        if not time_fits:
            available_slots = [
                f"{av.start_time.strftime('%H:%M')} - {av.end_time.strftime('%H:%M')}"
                for av in regular_availability
            ]
            raise ValidationError(
                f"Requested time slot does not fit artist's availability. "
                f"Available slots: {', '.join(available_slots)}"
            )

    # Check for conflicting bookings
    conflicting_bookings = Booking.objects.filter(
        artist=artist,
        booking_date=booking_date,
        status__in=[BookingStatus.PENDING, BookingStatus.ACCEPTED]
    ).filter(
        Q(start_time__lt=end_time, end_time__gt=start_time)  # Overlapping time slots
    )

    # Exclude current booking if updating
    if exclude_booking_id:
        conflicting_bookings = conflicting_bookings.exclude(id=exclude_booking_id)

    if conflicting_bookings.exists():
        return False

    return True


def get_available_time_slots(artist, booking_date, duration_minutes):
    """
    Get all available time slots for an artist on a given date.

    Args:
        artist: MakeupArtistProfile instance
        booking_date: date object
        duration_minutes: int, duration of the service

    Returns:
        list: List of available time slots as tuples (start_time, end_time)
    """
    available_slots = []

    # Check if artist is generally available
    if not artist.is_available:
        return available_slots

    # Check for availability exceptions
    exception = AvailabilityException.objects.filter(
        artist=artist,
        date=booking_date
    ).first()

    if exception and not exception.is_available:
        return available_slots

    # Determine available windows
    if exception and exception.start_time and exception.end_time:
        # Use exception availability
        windows = [(exception.start_time, exception.end_time)]
    else:
        # Use regular weekly availability
        day_of_week = booking_date.weekday()
        regular_availability = Availability.objects.filter(
            artist=artist,
            day_of_week=day_of_week,
            is_active=True
        )
        windows = [(av.start_time, av.end_time) for av in regular_availability]

    # Get existing bookings for the date
    existing_bookings = Booking.objects.filter(
        artist=artist,
        booking_date=booking_date,
        status__in=[BookingStatus.PENDING, BookingStatus.ACCEPTED]
    ).order_by('start_time')

    # Generate time slots for each window
    for window_start, window_end in windows:
        current_time = window_start
        slot_duration = timedelta(minutes=duration_minutes)

        while True:
            # Calculate end time for this slot
            end_datetime = datetime.combine(booking_date, current_time) + slot_duration
            end_time = end_datetime.time()

            # Check if slot fits within window
            if end_time > window_end:
                break

            # Check if slot conflicts with existing bookings
            conflicts = False
            for booking in existing_bookings:
                if (current_time < booking.end_time and end_time > booking.start_time):
                    conflicts = True
                    # Jump to after this booking
                    current_time = booking.end_time
                    break

            if not conflicts:
                available_slots.append((current_time, end_time))
                # Move to next slot (30-minute intervals)
                current_datetime = datetime.combine(booking_date, current_time) + timedelta(minutes=30)
                current_time = current_datetime.time()

    return available_slots


def generate_booking_number():
    """
    Generate a unique booking number.

    Returns:
        str: Unique booking number in format BK{timestamp}{random}
    """
    import uuid
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4())[:6].upper()
    return f"BK{timestamp}{random_suffix}"


def can_cancel_booking(booking, user):
    """
    Check if a user can cancel a booking.

    Args:
        booking: Booking instance
        user: User instance

    Returns:
        tuple: (bool, str) - (can_cancel, reason)
    """
    # Cannot cancel completed or already cancelled bookings
    if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
        return False, "Cannot cancel completed or already cancelled bookings."

    # Check if user is client or artist
    is_client = user == booking.client
    is_artist = hasattr(user, 'artist_profile') and user.artist_profile == booking.artist

    if not (is_client or is_artist):
        return False, "You don't have permission to cancel this booking."

    # Check cancellation deadline (e.g., 24 hours before)
    from django.utils import timezone
    booking_datetime = datetime.combine(booking.booking_date, booking.start_time)
    booking_datetime = timezone.make_aware(booking_datetime)
    time_until_booking = booking_datetime - timezone.now()

    # Allow cancellation up to 24 hours before
    if time_until_booking.total_seconds() < 24 * 3600:
        return False, "Bookings can only be cancelled at least 24 hours in advance."

    return True, ""


def get_booking_statistics(artist=None, client=None, date_from=None, date_to=None):
    """
    Get booking statistics for an artist or client.

    Args:
        artist: MakeupArtistProfile instance (optional)
        client: User instance (optional)
        date_from: date object (optional)
        date_to: date object (optional)

    Returns:
        dict: Statistics dictionary
    """
    from django.db.models import Count, Sum, Avg

    queryset = Booking.objects.all()

    if artist:
        queryset = queryset.filter(artist=artist)
    if client:
        queryset = queryset.filter(client=client)
    if date_from:
        queryset = queryset.filter(booking_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(booking_date__lte=date_to)

    stats = {
        'total_bookings': queryset.count(),
        'pending': queryset.filter(status=BookingStatus.PENDING).count(),
        'accepted': queryset.filter(status=BookingStatus.ACCEPTED).count(),
        'completed': queryset.filter(status=BookingStatus.COMPLETED).count(),
        'cancelled': queryset.filter(status=BookingStatus.CANCELLED).count(),
        'rejected': queryset.filter(status=BookingStatus.REJECTED).count(),
        'total_revenue': queryset.filter(
            status=BookingStatus.COMPLETED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'average_booking_value': queryset.filter(
            status=BookingStatus.COMPLETED
        ).aggregate(Avg('total_price'))['total_price__avg'] or 0,
    }

    return stats
