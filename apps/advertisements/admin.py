from django.contrib import admin
from .models import (
    AdvertisementPlan,
    VendorAdvertisementSubscription,
    Advertisement,
    AdvertisementPayment,
)

@admin.register(AdvertisementPlan)
class AdvertisementPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'validity_days', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(VendorAdvertisementSubscription)
class VendorAdvertisementSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'plan', 'start_date', 'end_date', 'is_active')
    search_fields = ('vendor__email', 'plan__name')
    list_filter = ('is_active', 'start_date', 'end_date')

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'subscription', 'redirect_url', 'created_at')
    search_fields = ('vendor__email', 'redirect_url')
    list_filter = ('created_at',)

@admin.register(AdvertisementPayment)
class AdvertisementPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'plan', 'razorpay_order_id', 'razorpay_payment_id', 'amount', 'status', 'created_at')
    search_fields = ('vendor__email', 'razorpay_order_id', 'razorpay_payment_id')
    list_filter = ('status', 'created_at')
