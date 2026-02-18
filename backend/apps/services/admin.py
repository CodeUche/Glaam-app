"""
Admin configuration for services app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Service, ServiceCategory


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model."""

    list_display = [
        'name',
        'artist_link',
        'category',
        'price_display',
        'duration_display',
        'is_active_display',
        'booking_count',
        'created_at',
    ]
    list_filter = ['category', 'is_active', 'created_at', 'updated_at']
    search_fields = [
        'name',
        'description',
        'artist__user__first_name',
        'artist__user__last_name',
        'artist__user__email',
    ]
    readonly_fields = ['id', 'booking_count', 'created_at', 'updated_at', 'duration_hours']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('Service Information', {
            'fields': ('id', 'artist', 'name', 'description', 'category')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration', 'duration_hours')
        }),
        ('Status & Metrics', {
            'fields': ('is_active', 'booking_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def artist_link(self, obj):
        """Display clickable link to artist profile."""
        url = reverse('admin:profiles_makeupartistprofile_change', args=[obj.artist.id])
        return format_html('<a href="{}">{}</a>', url, obj.artist.user.full_name)
    artist_link.short_description = 'Artist'

    def price_display(self, obj):
        """Display formatted price."""
        return f"${obj.price:,.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def duration_display(self, obj):
        """Display duration in hours and minutes."""
        hours = obj.duration // 60
        minutes = obj.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    duration_display.short_description = 'Duration'
    duration_display.admin_order_field = 'duration'

    def is_active_display(self, obj):
        """Display active status with colored icon."""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">&#10004; Active</span>'
            )
        return format_html(
            '<span style="color: red;">&#10008; Inactive</span>'
        )
    is_active_display.short_description = 'Status'
    is_active_display.admin_order_field = 'is_active'

    def duration_hours(self, obj):
        """Display duration in hours (read-only)."""
        return f"{obj.duration_hours} hours"
    duration_hours.short_description = 'Duration (Hours)'

    actions = ['activate_services', 'deactivate_services']

    def activate_services(self, request, queryset):
        """Bulk activate selected services."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} service(s) activated successfully.')
    activate_services.short_description = 'Activate selected services'

    def deactivate_services(self, request, queryset):
        """Bulk deactivate selected services."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} service(s) deactivated successfully.')
    deactivate_services.short_description = 'Deactivate selected services'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('artist', 'artist__user')
