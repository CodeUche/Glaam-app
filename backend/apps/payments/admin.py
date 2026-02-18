from django.contrib import admin
from .models import Payment, PayoutRecord


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'artist', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['client__email', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']


@admin.register(PayoutRecord)
class PayoutRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'artist', 'amount', 'status', 'period_start', 'period_end', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['artist__user__email']
    readonly_fields = ['created_at', 'processed_at']
    ordering = ['-created_at']
