"""
Filters for makeup artist profiles.
"""

import django_filters
from django.db.models import Q
from .models import MakeupArtistProfile


class MakeupArtistFilter(django_filters.FilterSet):
    """
    Advanced filter for makeup artist profiles.

    Supports filtering by:
    - Location (exact or search)
    - Rating (minimum threshold)
    - Specialties
    - Price range (hourly rate)
    - Availability status
    - Verification status
    - Years of experience
    """

    # Location filters
    location = django_filters.CharFilter(
        field_name='location',
        lookup_expr='icontains',
        help_text='Filter by location (partial match)'
    )
    location_exact = django_filters.CharFilter(
        field_name='location',
        lookup_expr='iexact',
        help_text='Filter by exact location match'
    )

    # Rating filters
    min_rating = django_filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte',
        help_text='Minimum average rating (0-5)'
    )
    rating = django_filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte',
        help_text='Alias for min_rating'
    )

    # Specialty filters
    specialty = django_filters.CharFilter(
        method='filter_specialty',
        help_text='Filter by specialty (e.g., bridal, editorial, glam)'
    )
    specialties = django_filters.CharFilter(
        method='filter_specialties_multiple',
        help_text='Filter by multiple specialties (comma-separated)'
    )

    # Price range filters
    min_price = django_filters.NumberFilter(
        field_name='hourly_rate',
        lookup_expr='gte',
        help_text='Minimum hourly rate'
    )
    max_price = django_filters.NumberFilter(
        field_name='hourly_rate',
        lookup_expr='lte',
        help_text='Maximum hourly rate'
    )
    price_range = django_filters.CharFilter(
        method='filter_price_range',
        help_text='Price range: budget (<50), moderate (50-100), premium (>100)'
    )

    # Availability filter
    available = django_filters.BooleanFilter(
        field_name='is_available',
        help_text='Filter by availability status'
    )

    # Verification filter
    verified = django_filters.BooleanFilter(
        field_name='verified',
        help_text='Filter by verification status'
    )

    # Experience filters
    min_experience = django_filters.NumberFilter(
        field_name='years_of_experience',
        lookup_expr='gte',
        help_text='Minimum years of experience'
    )
    max_experience = django_filters.NumberFilter(
        field_name='years_of_experience',
        lookup_expr='lte',
        help_text='Maximum years of experience'
    )
    experience_level = django_filters.CharFilter(
        method='filter_experience_level',
        help_text='Experience level: beginner (<2), intermediate (2-5), expert (>5)'
    )

    # Search filter (searches across multiple fields)
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search across name, bio, location, and specialties'
    )

    # Sorting
    ordering = django_filters.OrderingFilter(
        fields=(
            ('average_rating', 'rating'),
            ('hourly_rate', 'price'),
            ('years_of_experience', 'experience'),
            ('total_reviews', 'reviews'),
            ('total_bookings', 'bookings'),
            ('created_at', 'newest'),
        ),
        help_text='Order results by: rating, price, experience, reviews, bookings, newest'
    )

    class Meta:
        model = MakeupArtistProfile
        fields = [
            'location',
            'location_exact',
            'min_rating',
            'rating',
            'specialty',
            'specialties',
            'min_price',
            'max_price',
            'price_range',
            'available',
            'verified',
            'min_experience',
            'max_experience',
            'experience_level',
            'search',
            'ordering'
        ]

    def filter_specialty(self, queryset, name, value):
        """
        Filter by a single specialty.
        Uses PostgreSQL array contains operator.
        """
        if not value:
            return queryset

        value = value.lower().strip()

        # Validate specialty
        valid_specialties = [choice[0] for choice in MakeupArtistProfile.SPECIALTY_CHOICES]
        if value not in valid_specialties:
            return queryset.none()

        return queryset.filter(specialties__contains=[value])

    def filter_specialties_multiple(self, queryset, name, value):
        """
        Filter by multiple specialties (comma-separated).
        Returns artists that have ANY of the specified specialties.
        """
        if not value:
            return queryset

        # Parse comma-separated specialties
        specialties = [s.strip().lower() for s in value.split(',') if s.strip()]

        if not specialties:
            return queryset

        # Validate specialties
        valid_specialties = [choice[0] for choice in MakeupArtistProfile.SPECIALTY_CHOICES]
        specialties = [s for s in specialties if s in valid_specialties]

        if not specialties:
            return queryset.none()

        # Filter artists that have any of the specified specialties
        q_objects = Q()
        for specialty in specialties:
            q_objects |= Q(specialties__contains=[specialty])

        return queryset.filter(q_objects)

    def filter_price_range(self, queryset, name, value):
        """
        Filter by predefined price ranges.

        Ranges:
        - budget: < $50/hour
        - moderate: $50-100/hour
        - premium: > $100/hour
        """
        if not value:
            return queryset

        value = value.lower().strip()

        if value == 'budget':
            return queryset.filter(hourly_rate__lt=50)
        elif value == 'moderate':
            return queryset.filter(hourly_rate__gte=50, hourly_rate__lte=100)
        elif value == 'premium':
            return queryset.filter(hourly_rate__gt=100)
        else:
            return queryset

    def filter_experience_level(self, queryset, name, value):
        """
        Filter by predefined experience levels.

        Levels:
        - beginner: < 2 years
        - intermediate: 2-5 years
        - expert: > 5 years
        """
        if not value:
            return queryset

        value = value.lower().strip()

        if value == 'beginner':
            return queryset.filter(years_of_experience__lt=2)
        elif value == 'intermediate':
            return queryset.filter(years_of_experience__gte=2, years_of_experience__lte=5)
        elif value == 'expert':
            return queryset.filter(years_of_experience__gt=5)
        else:
            return queryset

    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields.

        Searches in:
        - Artist's full name
        - Bio
        - Location
        - Specialties
        """
        if not value:
            return queryset

        value = value.strip()

        return queryset.filter(
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(bio__icontains=value) |
            Q(location__icontains=value) |
            Q(specialties__contains=[value.lower()])
        ).distinct()


class PortfolioImageFilter(django_filters.FilterSet):
    """Filter for portfolio images."""

    category = django_filters.CharFilter(
        field_name='category',
        lookup_expr='exact',
        help_text='Filter by category'
    )

    is_featured = django_filters.BooleanFilter(
        field_name='is_featured',
        help_text='Filter by featured status'
    )

    artist = django_filters.UUIDFilter(
        field_name='artist__id',
        help_text='Filter by artist ID'
    )

    ordering = django_filters.OrderingFilter(
        fields=(
            ('display_order', 'order'),
            ('created_at', 'newest'),
        ),
        help_text='Order by: order, newest'
    )

    class Meta:
        from .models import PortfolioImage
        model = PortfolioImage
        fields = ['category', 'is_featured', 'artist', 'ordering']
