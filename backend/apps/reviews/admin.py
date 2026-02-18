"""
Admin configuration for reviews app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""

    list_display = [
        'id',
        'client_name',
        'artist_name',
        'rating_display',
        'is_visible',
        'flagged',
        'has_artist_response',
        'created_at'
    ]
    list_filter = [
        'rating',
        'is_visible',
        'flagged',
        'created_at',
        'responded_at'
    ]
    search_fields = [
        'client__email',
        'client__first_name',
        'client__last_name',
        'artist__user__email',
        'artist__user__first_name',
        'artist__user__last_name',
        'comment',
        'artist_response',
        'booking__booking_number'
    ]
    readonly_fields = [
        'id',
        'booking',
        'client',
        'artist',
        'created_at',
        'updated_at',
        'responded_at'
    ]
    fieldsets = (
        ('Review Information', {
            'fields': (
                'id',
                'booking',
                'client',
                'artist',
                'rating',
                'comment'
            )
        }),
        ('Visibility & Moderation', {
            'fields': (
                'is_visible',
                'flagged',
                'flagged_reason'
            )
        }),
        ('Artist Response', {
            'fields': (
                'artist_response',
                'responded_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50

    def client_name(self, obj):
        """Display client name."""
        return obj.client.full_name
    client_name.short_description = 'Client'
    client_name.admin_order_field = 'client__first_name'

    def artist_name(self, obj):
        """Display artist name."""
        return obj.artist.user.full_name
    artist_name.short_description = 'Artist'
    artist_name.admin_order_field = 'artist__user__first_name'

    def rating_display(self, obj):
        """Display rating with stars."""
        stars = '⭐' * obj.rating
        color = 'green' if obj.rating >= 4 else 'orange' if obj.rating >= 3 else 'red'
        return format_html(
            '<span style="color: {};">{} ({})</span>',
            color,
            stars,
            obj.rating
        )
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'

    def has_artist_response(self, obj):
        """Check if artist has responded."""
        if obj.artist_response:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">—</span>')
    has_artist_response.short_description = 'Response'
    has_artist_response.admin_order_field = 'responded_at'

    actions = ['flag_reviews', 'unflag_reviews', 'hide_reviews', 'show_reviews']

    def flag_reviews(self, request, queryset):
        """Flag selected reviews for moderation."""
        updated = queryset.update(flagged=True)
        self.message_user(request, f'{updated} review(s) flagged for moderation.')
    flag_reviews.short_description = 'Flag selected reviews'

    def unflag_reviews(self, request, queryset):
        """Remove flag from selected reviews."""
        updated = queryset.update(flagged=False, flagged_reason=None)
        self.message_user(request, f'{updated} review(s) unflagged.')
    unflag_reviews.short_description = 'Unflag selected reviews'

    def hide_reviews(self, request, queryset):
        """Hide selected reviews from public view."""
        updated = queryset.update(is_visible=False)
        self.message_user(request, f'{updated} review(s) hidden from public view.')
    hide_reviews.short_description = 'Hide selected reviews'

    def show_reviews(self, request, queryset):
        """Make selected reviews visible to public."""
        updated = queryset.update(is_visible=True)
        self.message_user(request, f'{updated} review(s) made visible.')
    show_reviews.short_description = 'Show selected reviews'
