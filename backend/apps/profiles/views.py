"""
Views for the profiles app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q, Count, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
import hashlib
import json

from .models import (
    ClientProfile,
    MakeupArtistProfile,
    PortfolioImage,
    Favorite,
    Availability,
    AvailabilityException
)
from .serializers import (
    ClientProfileSerializer,
    MakeupArtistProfileSerializer,
    MakeupArtistProfileReadSerializer,
    MakeupArtistProfileWriteSerializer,
    MakeupArtistListSerializer,
    PortfolioImageSerializer,
    FavoriteSerializer,
    AvailabilitySerializer,
    AvailabilityExceptionSerializer
)
from .filters import MakeupArtistFilter, PortfolioImageFilter
from .permissions import (
    IsArtist,
    IsClient,
    IsOwnerOrReadOnly,
    IsArtistOwnerOrReadOnly,
    CanManageAvailability,
    CanManagePortfolio
)


def generate_cache_key(prefix, **kwargs):
    """
    Generate a cache key from prefix and keyword arguments.
    """
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    key_string = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
    # Hash long keys to prevent key length issues
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    return key_string


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for client profiles.

    Clients can view and update their own profile.
    """
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = ClientProfile.objects.select_related('user').all()

    def get_queryset(self):
        """Filter to only show the authenticated user's profile."""
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def get_object(self):
        """Get the current user's client profile."""
        if self.kwargs.get('pk') == 'me':
            try:
                return self.get_queryset().get(user=self.request.user)
            except ClientProfile.DoesNotExist:
                raise NotFound("Client profile not found for this user.")
        return super().get_object()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update the current user's profile.
        """
        try:
            profile = ClientProfile.objects.select_related('user').get(user=request.user)
        except ClientProfile.DoesNotExist:
            return Response(
                {'error': 'Client profile not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        # PUT or PATCH
        serializer = self.get_serializer(profile, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MakeupArtistProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for makeup artist profiles.

    List and Detail: Public (read-only)
    Create, Update, Delete: Artist only (their own profile)

    Includes filtering, search, and ordering capabilities with caching.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MakeupArtistFilter
    search_fields = ['user__first_name', 'user__last_name', 'bio', 'location']
    ordering_fields = ['average_rating', 'hourly_rate', 'years_of_experience', 'total_reviews', 'created_at']
    ordering = ['-average_rating', '-total_reviews']

    def get_queryset(self):
        """
        Optimize query with prefetch_related, annotations, and caching.
        """
        # Build base queryset with optimizations
        queryset = MakeupArtistProfile.objects.select_related('user').prefetch_related(
            Prefetch(
                'portfolio_images',
                queryset=PortfolioImage.objects.order_by('display_order', '-created_at')
            ),
            'availabilities'
        )

        # Annotate with favorites count for optimization
        queryset = queryset.annotate(
            favorites_count=Count('favorited_by', distinct=True)
        )

        # For authenticated users, annotate if they've favorited each artist
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                _is_favorited=Exists(
                    Favorite.objects.filter(
                        client=self.request.user,
                        artist=OuterRef('pk')
                    )
                )
            )

        # Show all artists to staff, only available ones to public by default
        if not self.request.user.is_staff:
            show_unavailable = self.request.query_params.get('show_unavailable', 'false').lower() == 'true'
            if not show_unavailable:
                queryset = queryset.filter(is_available=True)

        return queryset

    def get_serializer_class(self):
        """Use different serializers for different operations."""
        if self.action in ['create', 'update', 'partial_update']:
            return MakeupArtistProfileWriteSerializer
        elif self.action == 'list':
            # Use optimized list serializer for listings
            return MakeupArtistListSerializer
        return MakeupArtistProfileReadSerializer

    def list(self, request, *args, **kwargs):
        """
        List artists with caching based on query parameters.
        Cache key includes filters, search, ordering, and pagination.
        """
        # Generate cache key from query parameters
        query_params = dict(request.query_params)
        query_params.pop('page', None)  # Don't include page in cache key for base query

        cache_key = generate_cache_key(
            'artist_list',
            user_id=request.user.id if request.user.is_authenticated else 'anonymous',
            **query_params
        )

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None and not request.user.is_staff:
            # Return cached data for non-staff users
            return Response(cached_data)

        # If not in cache, process the request
        response = super().list(request, *args, **kwargs)

        # Cache the response for 5 minutes (300 seconds)
        if response.status_code == 200:
            cache.set(cache_key, response.data, 300)

        return response

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve artist profile with caching.
        Cache individual profiles for 10 minutes.
        """
        artist_id = kwargs.get('pk')

        # Handle 'me' endpoint separately (no caching for personal data)
        if artist_id == 'me':
            return super().retrieve(request, *args, **kwargs)

        # Generate cache key for this artist
        cache_key = generate_cache_key(
            'artist_detail',
            artist_id=artist_id,
            user_id=request.user.id if request.user.is_authenticated else 'anonymous'
        )

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # If not in cache, process the request
        response = super().retrieve(request, *args, **kwargs)

        # Cache the response for 10 minutes (600 seconds)
        if response.status_code == 200:
            cache.set(cache_key, response.data, 600)

        return response

    def get_permissions(self):
        """Allow anyone to view, but only artists to modify."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsArtist()]
        return super().get_permissions()

    def get_object(self):
        """Get artist profile, handling 'me' as special case."""
        if self.kwargs.get('pk') == 'me':
            if not self.request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            try:
                return self.get_queryset().get(user=self.request.user)
            except MakeupArtistProfile.DoesNotExist:
                raise NotFound("Artist profile not found for this user.")
        return super().get_object()

    def perform_create(self, serializer):
        """Create artist profile for the current user."""
        # Check if profile already exists
        if MakeupArtistProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError("Artist profile already exists for this user.")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Ensure user can only update their own profile and invalidate cache."""
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own profile.")

        instance = serializer.save()

        # Invalidate cache for this artist
        self._invalidate_artist_cache(instance.id)

    def perform_destroy(self, instance):
        """Delete profile and invalidate cache."""
        artist_id = instance.id
        super().perform_destroy(instance)
        self._invalidate_artist_cache(artist_id)

    def _invalidate_artist_cache(self, artist_id):
        """
        Invalidate all cache entries related to an artist.
        This includes detail views and list views.
        """
        # Invalidate detail cache for all users
        cache.delete_many([
            generate_cache_key('artist_detail', artist_id=artist_id, user_id='anonymous'),
            generate_cache_key('artist_detail', artist_id=artist_id, user_id=self.request.user.id)
        ])

        # Pattern-based cache deletion for list views would require redis keys scan
        # For now, we'll use a simpler approach: invalidate on write
        # In production, consider using cache tags or versioning
        cache_pattern = f"artist_list:*"
        # Note: This would need django-redis for pattern matching
        try:
            cache.delete_pattern(cache_pattern)
        except AttributeError:
            # Fallback if delete_pattern is not available
            pass

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update the current user's artist profile.
        """
        if request.user.role != 'artist':
            return Response(
                {'error': 'Only artists can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            profile = self.get_queryset().get(user=request.user)
        except MakeupArtistProfile.DoesNotExist:
            return Response(
                {'error': 'Artist profile not found. Please create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'GET':
            serializer = MakeupArtistProfileReadSerializer(profile, context={'request': request})
            return Response(serializer.data)

        # PUT or PATCH
        serializer = MakeupArtistProfileWriteSerializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return the updated profile with read serializer
        read_serializer = MakeupArtistProfileReadSerializer(profile, context={'request': request})
        return Response(read_serializer.data)

    @action(detail=True, methods=['get'])
    def portfolio(self, request, pk=None):
        """
        Get all portfolio images for a specific artist.
        """
        artist = self.get_object()
        images = artist.portfolio_images.all()

        # Apply optional category filter
        category = request.query_params.get('category')
        if category:
            images = images.filter(category=category)

        serializer = PortfolioImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get availability schedule for a specific artist.
        """
        artist = self.get_object()
        availabilities = artist.availabilities.filter(is_active=True)
        serializer = AvailabilitySerializer(availabilities, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """
        Toggle favorite status for an artist.
        """
        artist = self.get_object()

        # Check if already favorited
        favorite = Favorite.objects.filter(client=request.user, artist=artist).first()

        if favorite:
            # Remove from favorites
            favorite.delete()
            is_favorited = False
            message = 'Artist removed from favorites.'
        else:
            # Add to favorites
            Favorite.objects.create(client=request.user, artist=artist)
            is_favorited = True
            message = 'Artist added to favorites.'

        # Invalidate cache for this artist (favorites count changed)
        self._invalidate_artist_cache(artist.id)

        return Response(
            {'message': message, 'is_favorited': is_favorited},
            status=status.HTTP_200_OK
        )


class PortfolioImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for portfolio images.

    List and Detail: Public (read-only)
    Create, Update, Delete: Artist only (their own images)
    """
    serializer_class = PortfolioImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PortfolioImageFilter
    ordering_fields = ['display_order', 'created_at']
    ordering = ['display_order', '-created_at']

    def get_queryset(self):
        """Get portfolio images, filtered by artist if specified."""
        queryset = PortfolioImage.objects.select_related('artist__user').all()

        # Filter by artist if specified
        artist_id = self.request.query_params.get('artist')
        if artist_id:
            queryset = queryset.filter(artist__id=artist_id)

        return queryset

    def get_permissions(self):
        """Allow anyone to view, but only artists to modify."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsArtist()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create portfolio image for the current user's artist profile."""
        try:
            artist_profile = self.request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            raise ValidationError("Artist profile not found for this user.")

        instance = serializer.save(artist=artist_profile)

        # Invalidate artist cache
        self._invalidate_artist_cache(artist_profile.id)

    def perform_update(self, serializer):
        """Ensure artist can only update their own portfolio images."""
        if serializer.instance.artist.user != self.request.user:
            raise PermissionDenied("You can only update your own portfolio images.")

        instance = serializer.save()

        # Invalidate artist cache
        self._invalidate_artist_cache(instance.artist.id)

    def perform_destroy(self, instance):
        """Ensure artist can only delete their own portfolio images."""
        if instance.artist.user != self.request.user:
            raise PermissionDenied("You can only delete your own portfolio images.")

        artist_id = instance.artist.id
        instance.delete()

        # Invalidate artist cache
        self._invalidate_artist_cache(artist_id)

    def _invalidate_artist_cache(self, artist_id):
        """Invalidate cache for artist when portfolio changes."""
        try:
            # Delete specific artist detail cache
            cache.delete_pattern(f"artist_detail:artist_id={artist_id}:*")
            # Delete list caches as they may include this artist
            cache.delete_pattern("artist_list:*")
        except AttributeError:
            # Fallback if delete_pattern is not available
            cache.delete(generate_cache_key('artist_detail', artist_id=artist_id, user_id='anonymous'))

    @action(detail=False, methods=['get'], permission_classes=[IsArtist])
    def my_portfolio(self, request):
        """
        Get all portfolio images for the current artist.
        """
        try:
            artist_profile = request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            return Response(
                {'error': 'Artist profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        images = PortfolioImage.objects.filter(artist=artist_profile)
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsArtist])
    def toggle_featured(self, request, pk=None):
        """
        Toggle featured status for a portfolio image.
        """
        image = self.get_object()

        # Ensure ownership
        if image.artist.user != request.user:
            raise PermissionDenied("You can only modify your own portfolio images.")

        # Toggle featured status
        image.is_featured = not image.is_featured
        image.save()

        # Invalidate artist cache
        self._invalidate_artist_cache(image.artist.id)

        serializer = self.get_serializer(image)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsArtist])
    def reorder(self, request):
        """
        Reorder portfolio images.

        Expects a list of image IDs in the desired order.
        Example: {"image_ids": ["uuid1", "uuid2", "uuid3"]}
        """
        image_ids = request.data.get('image_ids', [])

        if not image_ids:
            raise ValidationError("image_ids list is required.")

        try:
            artist_profile = request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            return Response(
                {'error': 'Artist profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify all images belong to the artist
        images = PortfolioImage.objects.filter(id__in=image_ids, artist=artist_profile)

        if images.count() != len(image_ids):
            raise ValidationError("Some image IDs are invalid or don't belong to you.")

        # Update display order
        for index, image_id in enumerate(image_ids):
            PortfolioImage.objects.filter(id=image_id).update(display_order=index)

        # Invalidate artist cache
        self._invalidate_artist_cache(artist_profile.id)

        return Response({'message': 'Portfolio images reordered successfully.'})


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing favorite artists.

    Only authenticated users can manage their favorites.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get favorites for the current user."""
        return Favorite.objects.filter(
            client=self.request.user
        ).select_related(
            'artist__user'
        ).prefetch_related(
            'artist__portfolio_images'
        )

    def perform_create(self, serializer):
        """Create favorite for the current user."""
        instance = serializer.save(client=self.request.user)

        # Invalidate cache for the favorited artist
        self._invalidate_artist_cache(instance.artist.id)

    def perform_destroy(self, instance):
        """Ensure user can only delete their own favorites."""
        if instance.client != self.request.user:
            raise PermissionDenied("You can only delete your own favorites.")

        artist_id = instance.artist.id
        instance.delete()

        # Invalidate cache for the artist
        self._invalidate_artist_cache(artist_id)

    def _invalidate_artist_cache(self, artist_id):
        """Invalidate cache for artist when favorites change."""
        try:
            cache.delete_pattern(f"artist_detail:artist_id={artist_id}:*")
            cache.delete_pattern("artist_list:*")
        except AttributeError:
            cache.delete(generate_cache_key('artist_detail', artist_id=artist_id, user_id='anonymous'))

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        """
        Get all favorite artists for the current user.
        """
        favorites = self.get_queryset()
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)


class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing artist availability.

    Only artists can manage their own availability.
    """
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get availability for the current artist or filter by artist_id."""
        queryset = Availability.objects.select_related('artist__user').all()

        # Filter by artist if specified
        artist_id = self.request.query_params.get('artist')
        if artist_id:
            queryset = queryset.filter(artist__id=artist_id)
        elif self.request.user.role == 'artist':
            # For artists, default to their own availability
            try:
                queryset = queryset.filter(artist=self.request.user.artist_profile)
            except MakeupArtistProfile.DoesNotExist:
                return queryset.none()

        return queryset

    def get_permissions(self):
        """Allow anyone to view, but only artists to modify."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsArtist()]

    def perform_create(self, serializer):
        """Create availability for the current artist."""
        try:
            artist_profile = self.request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            raise ValidationError("Artist profile not found for this user.")

        serializer.save(artist=artist_profile)

    def perform_update(self, serializer):
        """Ensure artist can only update their own availability."""
        if serializer.instance.artist.user != self.request.user:
            raise PermissionDenied("You can only update your own availability.")
        serializer.save()

    def perform_destroy(self, instance):
        """Ensure artist can only delete their own availability."""
        if instance.artist.user != self.request.user:
            raise PermissionDenied("You can only delete your own availability.")
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsArtist])
    def my_schedule(self, request):
        """
        Get the complete availability schedule for the current artist.
        """
        try:
            artist_profile = request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            return Response(
                {'error': 'Artist profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        availabilities = Availability.objects.filter(artist=artist_profile).order_by('day_of_week', 'start_time')
        serializer = self.get_serializer(availabilities, many=True)
        return Response(serializer.data)


class AvailabilityExceptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing availability exceptions.

    Only artists can manage their own availability exceptions.
    """
    serializer_class = AvailabilityExceptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get availability exceptions for the current artist or filter by artist_id."""
        queryset = AvailabilityException.objects.select_related('artist__user').all()

        # Filter by artist if specified
        artist_id = self.request.query_params.get('artist')
        if artist_id:
            queryset = queryset.filter(artist__id=artist_id)
        elif self.request.user.role == 'artist':
            # For artists, default to their own exceptions
            try:
                queryset = queryset.filter(artist=self.request.user.artist_profile)
            except MakeupArtistProfile.DoesNotExist:
                return queryset.none()

        # Filter out past exceptions by default
        show_past = self.request.query_params.get('show_past', 'false').lower() == 'true'
        if not show_past:
            queryset = queryset.filter(date__gte=timezone.now().date())

        return queryset.order_by('date')

    def get_permissions(self):
        """Allow anyone to view, but only artists to modify."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsArtist()]

    def perform_create(self, serializer):
        """Create availability exception for the current artist."""
        try:
            artist_profile = self.request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            raise ValidationError("Artist profile not found for this user.")

        serializer.save(artist=artist_profile)

    def perform_update(self, serializer):
        """Ensure artist can only update their own availability exceptions."""
        if serializer.instance.artist.user != self.request.user:
            raise PermissionDenied("You can only update your own availability exceptions.")
        serializer.save()

    def perform_destroy(self, instance):
        """Ensure artist can only delete their own availability exceptions."""
        if instance.artist.user != self.request.user:
            raise PermissionDenied("You can only delete your own availability exceptions.")
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsArtist])
    def my_exceptions(self, request):
        """
        Get all availability exceptions for the current artist.
        """
        try:
            artist_profile = request.user.artist_profile
        except MakeupArtistProfile.DoesNotExist:
            return Response(
                {'error': 'Artist profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        exceptions = AvailabilityException.objects.filter(
            artist=artist_profile,
            date__gte=timezone.now().date()
        ).order_by('date')

        serializer = self.get_serializer(exceptions, many=True)
        return Response(serializer.data)
