from django.contrib import admin
from .models import Package, Subscription
from unfold.admin import ModelAdmin

# Register your models here.
@admin.register(Package)
class PackageAdmin(ModelAdmin):
    list_display = ('id', 'name', 'price', 'interval', 'discount', 'discount_price', 'is_active')
    list_display_links = ('id', 'name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'price', 'description', 'interval', 'is_active')
        }),
        ('Discount', {
            'fields': ('discount', 'discount_price')
        }),
        ('Stripe Configuration', {
            'fields': ('stripe_product_id', 'stripe_price_id'),
            'classes': ('collapse',)
        }),
        ('PayPal Configuration', {
            'fields': ('paypal_product_id', 'paypal_plan_id'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('id', 'user', 'package', 'payment_method', 'start_date', 'end_date', 'is_active')
    list_display_links = ('id', 'user', 'package',)
    list_filter = ('payment_method', 'is_active')
    search_fields = ('user__email', 'user__name',)
    readonly_fields = ('start_date', 'end_date', 'stripe_subscription_id', 'paypal_subscription_id')
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'package', 'payment_method', 'is_active', 'start_date', 'end_date')
        }),
        ('Payment Gateway IDs', {
            'fields': ('stripe_subscription_id', 'paypal_subscription_id'),
        }),
    )