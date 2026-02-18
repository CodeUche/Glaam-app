"""
Views for reviews app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import Review
from .serializers import (
    ReviewListSerializer,
    ReviewDetailSerializer,
    ReviewCreateSerializer,
    ArtistResponseSerializer,
    ReviewModerationSerializer,
    ReviewStatsSerializer,
)
from .permissions import (
    IsClient,
    IsArtist,
    IsReviewArtist,
    CanViewReview,
    CanModerateReview,
    CanCreateReview,
)
from .filters import ReviewFilter


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.

    Endpoints:
    - GET /reviews/ - List reviews (with filters)
    - POST /reviews/ - Create review (clients only, completed bookings)
    - GET /reviews/{id}/ - Get review detail
    - PATCH /reviews/{id}/respond/ - Artist response
    - PATCH /reviews/{id}/moderate/ - Admin moderation
    - GET /reviews/stats/ - Review statistics
    - GET /reviews/my-reviews/ - Current user's reviews
    """

    queryset = Review.objects.select_related(
        'client',
        'artist',
        'artist__user',
        'booking'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReviewFilter
    search_fields = ['comment', 'artist_response', 'client__first_name', 'client__last_name']
    ordering_fields = ['rating', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action == 'respond':
            return ArtistResponseSerializer
        elif self.action == 'moderate':
            return ReviewModerationSerializer
        elif self.action == 'retrieve':
            return ReviewDetailSerializer
        elif self.action == 'stats':
            return ReviewStatsSerializer
        return ReviewListSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanCreateReview]
        elif self.action == 'respond':
            permission_classes = [IsAuthenticated, IsArtist, IsReviewArtist]
        elif self.action == 'moderate':
            permission_classes = [IsAuthenticated, CanModerateReview]
        elif self.action in ['list', 'retrieve', 'stats']:
            permission_classes = [AllowAny]
        elif self.action == 'my_reviews':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanModerateReview]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user and visibility.

        - Public users see only visible reviews
        - Clients see their own reviews (even if hidden)
        - Artists see reviews about them (even if hidden)
        - Admins see all reviews
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by artist if provided
        artist_id = self.request.query_params.get('artist', None)
        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)

        # Filter by client if provided
        client_id = self.request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        # Admin sees all
        if user.is_authenticated and user.is_admin_user:
            return queryset

        # Artist sees reviews about them
        if user.is_authenticated and hasattr(user, 'artist_profile'):
            return queryset.filter(
                Q(is_visible=True) | Q(artist=user.artist_profile)
            )

        # Client sees their own reviews
        if user.is_authenticated and user.role == 'client':
            return queryset.filter(
                Q(is_visible=True) | Q(client=user)
            )

        # Public sees only visible reviews
        return queryset.filter(is_visible=True)

    def perform_create(self, serializer):
        """Create review and trigger rating update."""
        review = serializer.save()

        # Trigger async rating update task
        from .tasks import update_artist_rating
        update_artist_rating.delay(str(review.artist.id))

    @action(detail=True, methods=['patch'], url_path='respond')
    def respond(self, request, pk=None):
        """
        Artist response endpoint.

        POST /reviews/{id}/respond/
        {
            "response": "Thank you for the review!"
        }
        """
        review = self.get_object()

        # Check permission
        self.check_object_permissions(request, review)

        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='moderate')
    def moderate(self, request, pk=None):
        """
        Admin moderation endpoint.

        PATCH /reviews/{id}/moderate/
        {
            "action": "flag|unflag|hide|show",
            "reason": "Spam content" (required for flag)
        }
        """
        review = self.get_object()

        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        action_name = request.data.get('action')
        return Response(
            {
                'message': f'Review {action_name}ed successfully.',
                'review': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='my-reviews')
    def my_reviews(self, request):
        """
        Get current user's reviews (for clients) or reviews about them (for artists).

        GET /reviews/my-reviews/
        """
        user = request.user

        if user.role == 'client':
            queryset = self.get_queryset().filter(client=user)
        elif hasattr(user, 'artist_profile'):
            queryset = self.get_queryset().filter(artist=user.artist_profile)
        else:
            queryset = Review.objects.none()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ReviewListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ReviewListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get review statistics for an artist.

        GET /reviews/stats/?artist={artist_id}
        """
        artist_id = request.query_params.get('artist')
        if not artist_id:
            return Response(
                {'error': 'artist parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get visible reviews for the artist
        reviews = Review.objects.filter(
            artist_id=artist_id,
            is_visible=True
        )

        # Calculate statistics
        total_reviews = reviews.count()

        if total_reviews == 0:
            return Response({
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'recent_reviews_count': 0,
                'response_rate': 0
            })

        # Average rating
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = reviews.filter(rating=i).count()

        # Recent reviews (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews_count = reviews.filter(created_at__gte=thirty_days_ago).count()

        # Response rate
        reviews_with_response = reviews.exclude(artist_response__isnull=True).exclude(artist_response='').count()
        response_rate = (reviews_with_response / total_reviews * 100) if total_reviews > 0 else 0

        data = {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_distribution,
            'recent_reviews_count': recent_reviews_count,
            'response_rate': round(response_rate, 2)
        }

        serializer = ReviewStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='flagged')
    def flagged_reviews(self, request):
        """
        Get all flagged reviews (admin only).

        GET /reviews/flagged/
        """
        # Check admin permission
        if not (request.user.is_authenticated and request.user.is_admin_user):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset().filter(flagged=True)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ReviewListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ReviewListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
