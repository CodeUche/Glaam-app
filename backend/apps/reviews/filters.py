"""
Filters for reviews app.
"""

import django_filters
from django.db.models import Q
from .models import Review


class ReviewFilter(django_filters.FilterSet):
    """
    FilterSet for Review model.

    Supports filtering by:
    - artist: Filter by artist ID
    - client: Filter by client ID
    - rating: Exact rating or range (min_rating, max_rating)
    - has_response: Reviews with/without artist response
    - flagged: Show flagged reviews
    - is_visible: Show visible/hidden reviews
    - created_after: Reviews created after date
    - created_before: Reviews created before date
    """

    artist = django_filters.UUIDFilter(field_name='artist__id')
    client = django_filters.UUIDFilter(field_name='client__id')
    rating = django_filters.NumberFilter(field_name='rating')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    has_response = django_filters.BooleanFilter(method='filter_has_response')
    flagged = django_filters.BooleanFilter(field_name='flagged')
    is_visible = django_filters.BooleanFilter(field_name='is_visible')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    booking = django_filters.UUIDFilter(field_name='booking__id')

    class Meta:
        model = Review
        fields = [
            'artist',
            'client',
            'rating',
            'min_rating',
            'max_rating',
            'has_response',
            'flagged',
            'is_visible',
            'created_after',
            'created_before',
            'booking'
        ]

    def filter_has_response(self, queryset, name, value):
        """Filter reviews based on whether they have an artist response."""
        if value:
            # Has response
            return queryset.exclude(
                Q(artist_response__isnull=True) | Q(artist_response='')
            )
        else:
            # No response
            return queryset.filter(
                Q(artist_response__isnull=True) | Q(artist_response='')
            )
