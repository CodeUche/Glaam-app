"""
Admin configuration for bookings app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Booking, Service, BookingStatus


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model."""

    list_display = [
        'name', 'artist', 'price', 'duration_minutes',
        'category', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'artist__user__email', 'artist__user__first_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'artist', 'name', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration_minutes', 'category')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queries."""
        return super().get_queryset(request).select_related('artist__user')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model."""

    list_display = [
        'booking_number', 'get_client_name', 'get_artist_name',
        'booking_date', 'start_time', 'status_badge', 'total_price', 'created_at'
    ]
    list_filter = ['status', 'booking_date', 'created_at', 'cancelled_by']
    search_fields = [
        'booking_number', 'client__email', 'client__first_name',
        'artist__user__email', 'artist__user__first_name', 'location'
    ]
    readonly_fields = [
        'id', 'booking_number', 'created_at', 'updated_at',
        'accepted_at', 'completed_at', 'cancelled_at'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'booking_date'
    autocomplete_fields = ['client', 'artist', 'service']

    fieldsets = (
        ('Booking Information', {
            'fields': ('id', 'booking_number', 'client', 'artist', 'service')
        }),
        ('Schedule', {
            'fields': ('booking_date', 'start_time', 'end_time', 'location')
        }),
        ('Status & Notes', {
            'fields': ('status', 'client_notes', 'artist_notes')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancelled_by'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'accepted_at',
                'completed_at', 'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queries."""
        return super().get_queryset(request).select_related(
            'client', 'artist__user', 'service'
        )

    def get_client_name(self, obj):
        """Get client's full name."""
        return obj.client.full_name
    get_client_name.short_description = 'Client'
    get_client_name.admin_order_field = 'client__first_name'

    def get_artist_name(self, obj):
        """Get artist's full name."""
        return obj.artist.user.full_name
    get_artist_name.short_description = 'Artist'
    get_artist_name.admin_order_field = 'artist__user__first_name'

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            BookingStatus.PENDING: '#FFA500',  # Orange
            BookingStatus.ACCEPTED: '#28A745',  # Green
            BookingStatus.REJECTED: '#DC3545',  # Red
            BookingStatus.COMPLETED: '#007BFF',  # Blue
            BookingStatus.CANCELLED: '#6C757D',  # Gray
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['mark_as_completed', 'mark_as_cancelled']

    def mark_as_completed(self, request, queryset):
        """Bulk action to mark bookings as completed."""
        count = 0
        for booking in queryset.filter(status=BookingStatus.ACCEPTED):
            try:
                booking.complete()
                count += 1
            except Exception:
                pass
        self.message_user(request, f'{count} booking(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected bookings as completed'

    def mark_as_cancelled(self, request, queryset):
        """Bulk action to cancel bookings."""
        count = 0
        for booking in queryset.exclude(
            status__in=[BookingStatus.COMPLETED, BookingStatus.CANCELLED]
        ):
            try:
                booking.cancel(cancelled_by='admin', reason='Cancelled by administrator')
                count += 1
            except Exception:
                pass
        self.message_user(request, f'{count} booking(s) cancelled.')
    mark_as_cancelled.short_description = 'Cancel selected bookings'
