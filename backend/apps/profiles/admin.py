"""
Admin configuration for profiles app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ClientProfile,
    MakeupArtistProfile,
    PortfolioImage,
    Favorite,
    Availability,
    AvailabilityException
)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin interface for client profiles."""

    list_display = [
        'id',
        'user_link',
        'user_email',
        'preferred_location',
        'profile_photo_preview',
        'created_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'preferred_location',
        'bio'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'profile_photo_preview'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_photo', 'profile_photo_preview')
        }),
        ('Profile Details', {
            'fields': ('bio', 'preferred_location', 'notification_preferences')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        """Link to user admin page."""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'User'

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'

    def profile_photo_preview(self, obj):
        """Display profile photo preview."""
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.profile_photo.url
            )
        return '-'
    profile_photo_preview.short_description = 'Photo Preview'


class PortfolioImageInline(admin.TabularInline):
    """Inline admin for portfolio images."""

    model = PortfolioImage
    extra = 0
    fields = ['image_url', 'thumbnail_preview', 'category', 'display_order', 'is_featured', 'created_at']
    readonly_fields = ['thumbnail_preview', 'created_at']

    def thumbnail_preview(self, obj):
        """Display thumbnail preview."""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image_url.url
            )
        return '-'
    thumbnail_preview.short_description = 'Preview'


class AvailabilityInline(admin.TabularInline):
    """Inline admin for availability."""

    model = Availability
    extra = 0
    fields = ['day_of_week', 'start_time', 'end_time', 'is_active']


@admin.register(MakeupArtistProfile)
class MakeupArtistProfileAdmin(admin.ModelAdmin):
    """Admin interface for makeup artist profiles."""

    list_display = [
        'id',
        'user_link',
        'user_email',
        'location',
        'hourly_rate',
        'average_rating',
        'total_reviews',
        'total_bookings',
        'is_available',
        'verified',
        'created_at'
    ]
    list_filter = [
        'is_available',
        'verified',
        'specialties',
        'created_at',
        'updated_at'
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'location',
        'bio'
    ]
    readonly_fields = [
        'id',
        'average_rating',
        'total_reviews',
        'total_bookings',
        'created_at',
        'updated_at',
        'profile_photo_preview'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_photo', 'profile_photo_preview')
        }),
        ('Profile Details', {
            'fields': (
                'bio',
                'specialties',
                'years_of_experience',
                'hourly_rate',
                'is_available'
            )
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Statistics', {
            'fields': (
                'average_rating',
                'total_reviews',
                'total_bookings',
                'verified',
                'verification_date'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [PortfolioImageInline, AvailabilityInline]
    actions = ['verify_artists', 'unverify_artists', 'mark_available', 'mark_unavailable']

    def user_link(self, obj):
        """Link to user admin page."""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'User'

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'

    def profile_photo_preview(self, obj):
        """Display profile photo preview."""
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.profile_photo.url
            )
        return '-'
    profile_photo_preview.short_description = 'Photo Preview'

    def verify_artists(self, request, queryset):
        """Verify selected artists."""
        from django.utils import timezone
        count = queryset.update(verified=True, verification_date=timezone.now())
        self.message_user(request, f'{count} artist(s) verified successfully.')
    verify_artists.short_description = 'Verify selected artists'

    def unverify_artists(self, request, queryset):
        """Unverify selected artists."""
        count = queryset.update(verified=False, verification_date=None)
        self.message_user(request, f'{count} artist(s) unverified successfully.')
    unverify_artists.short_description = 'Unverify selected artists'

    def mark_available(self, request, queryset):
        """Mark artists as available."""
        count = queryset.update(is_available=True)
        self.message_user(request, f'{count} artist(s) marked as available.')
    mark_available.short_description = 'Mark as available'

    def mark_unavailable(self, request, queryset):
        """Mark artists as unavailable."""
        count = queryset.update(is_available=False)
        self.message_user(request, f'{count} artist(s) marked as unavailable.')
    mark_unavailable.short_description = 'Mark as unavailable'


@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    """Admin interface for portfolio images."""

    list_display = [
        'id',
        'artist_link',
        'thumbnail_preview',
        'category',
        'display_order',
        'is_featured',
        'created_at'
    ]
    list_filter = ['category', 'is_featured', 'created_at']
    search_fields = [
        'artist__user__email',
        'artist__user__first_name',
        'artist__user__last_name',
        'caption',
        'category'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'image_preview']
    fieldsets = (
        ('Image Information', {
            'fields': ('artist', 'image_url', 'image_preview', 'thumbnail_url', 'caption')
        }),
        ('Display Settings', {
            'fields': ('category', 'display_order', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_featured', 'unmark_featured']

    def artist_link(self, obj):
        """Link to artist admin page."""
        url = reverse('admin:profiles_makeupartistprofile_change', args=[obj.artist.id])
        return format_html('<a href="{}">{}</a>', url, obj.artist.user.full_name)
    artist_link.short_description = 'Artist'

    def thumbnail_preview(self, obj):
        """Display thumbnail preview."""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image_url.url
            )
        return '-'
    thumbnail_preview.short_description = 'Preview'

    def image_preview(self, obj):
        """Display full image preview."""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 400px; max-width: 400px;" />',
                obj.image_url.url
            )
        return '-'
    image_preview.short_description = 'Image Preview'

    def mark_featured(self, request, queryset):
        """Mark selected images as featured."""
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} image(s) marked as featured.')
    mark_featured.short_description = 'Mark as featured'

    def unmark_featured(self, request, queryset):
        """Unmark selected images as featured."""
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} image(s) unmarked as featured.')
    unmark_featured.short_description = 'Unmark as featured'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin interface for favorites."""

    list_display = [
        'id',
        'client_link',
        'artist_link',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = [
        'client__email',
        'client__first_name',
        'client__last_name',
        'artist__user__email',
        'artist__user__first_name',
        'artist__user__last_name'
    ]
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Favorite Information', {
            'fields': ('client', 'artist')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def client_link(self, obj):
        """Link to client user admin page."""
        url = reverse('admin:users_user_change', args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.full_name)
    client_link.short_description = 'Client'

    def artist_link(self, obj):
        """Link to artist admin page."""
        url = reverse('admin:profiles_makeupartistprofile_change', args=[obj.artist.id])
        return format_html('<a href="{}">{}</a>', url, obj.artist.user.full_name)
    artist_link.short_description = 'Artist'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """Admin interface for availability."""

    list_display = [
        'id',
        'artist_link',
        'day_of_week_display',
        'time_range',
        'is_active',
        'created_at'
    ]
    list_filter = ['day_of_week', 'is_active', 'created_at']
    search_fields = [
        'artist__user__email',
        'artist__user__first_name',
        'artist__user__last_name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Availability Information', {
            'fields': ('artist', 'day_of_week', 'start_time', 'end_time', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_availability', 'deactivate_availability']

    def artist_link(self, obj):
        """Link to artist admin page."""
        url = reverse('admin:profiles_makeupartistprofile_change', args=[obj.artist.id])
        return format_html('<a href="{}">{}</a>', url, obj.artist.user.full_name)
    artist_link.short_description = 'Artist'

    def day_of_week_display(self, obj):
        """Display day of week name."""
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = 'Day'

    def time_range(self, obj):
        """Display time range."""
        return f'{obj.start_time.strftime("%H:%M")} - {obj.end_time.strftime("%H:%M")}'
    time_range.short_description = 'Time Range'

    def activate_availability(self, request, queryset):
        """Activate selected availability slots."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} availability slot(s) activated.')
    activate_availability.short_description = 'Activate selected slots'

    def deactivate_availability(self, request, queryset):
        """Deactivate selected availability slots."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} availability slot(s) deactivated.')
    deactivate_availability.short_description = 'Deactivate selected slots'


@admin.register(AvailabilityException)
class AvailabilityExceptionAdmin(admin.ModelAdmin):
    """Admin interface for availability exceptions."""

    list_display = [
        'id',
        'artist_link',
        'date',
        'is_available',
        'time_range',
        'created_at'
    ]
    list_filter = ['is_available', 'date', 'created_at']
    search_fields = [
        'artist__user__email',
        'artist__user__first_name',
        'artist__user__last_name',
        'reason'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Exception Information', {
            'fields': ('artist', 'date', 'is_available', 'start_time', 'end_time', 'reason')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def artist_link(self, obj):
        """Link to artist admin page."""
        url = reverse('admin:profiles_makeupartistprofile_change', args=[obj.artist.id])
        return format_html('<a href="{}">{}</a>', url, obj.artist.user.full_name)
    artist_link.short_description = 'Artist'

    def time_range(self, obj):
        """Display time range if available."""
        if obj.start_time and obj.end_time:
            return f'{obj.start_time.strftime("%H:%M")} - {obj.end_time.strftime("%H:%M")}'
        return '-'
    time_range.short_description = 'Time Range'
