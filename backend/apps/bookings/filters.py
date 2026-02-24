"""
Filters for bookings app.
"""

import django_filters
from .models import Booking, BookingStatus
from apps.services.models import Service


class BookingFilter(django_filters.FilterSet):
    """Filter set for Booking model."""

    booking_date_from = django_filters.DateFilter(
        field_name='booking_date',
        lookup_expr='gte',
        label='Booking date from'
    )
    booking_date_to = django_filters.DateFilter(
        field_name='booking_date',
        lookup_expr='lte',
        label='Booking date to'
    )
    created_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created from'
    )
    created_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created to'
    )
    status = django_filters.MultipleChoiceFilter(
        choices=BookingStatus.choices,
        label='Status'
    )
    min_price = django_filters.NumberFilter(
        field_name='total_price',
        lookup_expr='gte',
        label='Minimum price'
    )
    max_price = django_filters.NumberFilter(
        field_name='total_price',
        lookup_expr='lte',
        label='Maximum price'
    )

    class Meta:
        model = Booking
        fields = [
            'status', 'booking_date', 'artist', 'service',
            'booking_date_from', 'booking_date_to',
            'created_from', 'created_to', 'min_price', 'max_price'
        ]


class ServiceFilter(django_filters.FilterSet):
    """Filter set for Service model."""

    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Minimum price'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Maximum price'
    )
    min_duration = django_filters.NumberFilter(
        field_name='duration',
        lookup_expr='gte',
        label='Minimum duration (minutes)'
    )
    max_duration = django_filters.NumberFilter(
        field_name='duration',
        lookup_expr='lte',
        label='Maximum duration (minutes)'
    )

    class Meta:
        model = Service
        fields = [
            'artist', 'category', 'is_active',
            'min_price', 'max_price', 'min_duration', 'max_duration'
        ]
