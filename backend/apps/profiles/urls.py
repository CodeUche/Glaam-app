"""
URL configuration for profiles app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientProfileViewSet,
    MakeupArtistProfileViewSet,
    PortfolioImageViewSet,
    FavoriteViewSet,
    AvailabilityViewSet,
    AvailabilityExceptionViewSet
)

app_name = 'profiles'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'clients', ClientProfileViewSet, basename='client-profile')
router.register(r'artists', MakeupArtistProfileViewSet, basename='artist-profile')
router.register(r'portfolio', PortfolioImageViewSet, basename='portfolio-image')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'availability', AvailabilityViewSet, basename='availability')
router.register(r'availability-exceptions', AvailabilityExceptionViewSet, basename='availability-exception')

urlpatterns = [
    path('', include(router.urls)),
]
