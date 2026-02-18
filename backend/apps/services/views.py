"""
Views for service management.
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Service, ServiceCategory
from .serializers import (
    ServiceSerializer,
    ServiceListSerializer,
    ServiceCreateUpdateSerializer,
)
from .permissions import IsArtistOwnerOrReadOnly, IsArtistOwner
from apps.users.permissions import IsArtist


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing makeup services.

    - List/Retrieve: Any authenticated user can view services
    - Create: Only artists can create services
    - Update/Delete: Only the artist who owns the service can modify it
    """

    queryset = Service.objects.select_related('artist', 'artist__user').all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsArtistOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'artist']
    search_fields = ['name', 'description', 'artist__user__first_name', 'artist__user__last_name']
    ordering_fields = ['price', 'duration', 'booking_count', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ServiceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer

    def get_queryset(self):
        """
        Filter queryset based on user and query parameters.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by minimum/maximum price
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by minimum/maximum duration
        min_duration = self.request.query_params.get('min_duration')
        max_duration = self.request.query_params.get('max_duration')
        if min_duration:
            queryset = queryset.filter(duration__gte=min_duration)
        if max_duration:
            queryset = queryset.filter(duration__lte=max_duration)

        # Show only active services to non-owners
        if user.is_authenticated and hasattr(user, 'artist_profile'):
            # Artists can see all their services
            artist_services = queryset.filter(artist=user.artist_profile)
            other_services = queryset.exclude(artist=user.artist_profile).filter(is_active=True)
            queryset = artist_services | other_services
        else:
            # Clients and anonymous users see only active services
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_serializer_context(self):
        """Add artist to serializer context."""
        context = super().get_serializer_context()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'artist_profile'):
            context['artist'] = self.request.user.artist_profile
        return context

    def perform_create(self, serializer):
        """Create service for the authenticated artist."""
        if not hasattr(self.request.user, 'artist_profile'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only makeup artists can create services.")

        serializer.save(artist=self.request.user.artist_profile)

    def perform_update(self, serializer):
        """Update service with updated timestamp."""
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsArtist])
    def my_services(self, request):
        """
        Get all services for the authenticated artist.
        Endpoint: GET /api/services/my_services/
        """
        if not hasattr(request.user, 'artist_profile'):
            return Response(
                {'error': 'Artist profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        services = self.get_queryset().filter(artist=request.user.artist_profile)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsArtistOwner])
    def toggle_active(self, request, pk=None):
        """
        Toggle service active status.
        Endpoint: POST /api/services/{id}/toggle_active/
        """
        service = self.get_object()
        service.is_active = not service.is_active
        service.save(update_fields=['is_active', 'updated_at'])

        serializer = self.get_serializer(service)
        return Response({
            'message': f'Service {"activated" if service.is_active else "deactivated"} successfully.',
            'service': serializer.data
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get available service categories.
        Endpoint: GET /api/services/categories/
        """
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in ServiceCategory.choices
        ]
        return Response(categories)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular services based on booking count.
        Endpoint: GET /api/services/popular/
        """
        popular_services = self.get_queryset().filter(
            is_active=True
        ).order_by('-booking_count')[:10]

        serializer = ServiceListSerializer(popular_services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def by_artist(self, request, pk=None):
        """
        Get all active services by a specific artist.
        Endpoint: GET /api/services/{artist_id}/by_artist/
        """
        services = self.get_queryset().filter(
            artist_id=pk,
            is_active=True
        )
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)
