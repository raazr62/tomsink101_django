from django.contrib import admin
from .models import Package, Subscription, PackageFeature, PricingSection
from unfold.admin import ModelAdmin, TabularInline


class PackageFeatureInline(TabularInline):
    model = PackageFeature
    extra = 1
    fields = ('feature_text', 'is_included', 'order')


# Register your models here.
@admin.register(Package)
class PackageAdmin(ModelAdmin):
    list_display = ('id', 'name', 'price', 'interval', 'discount', 'discount_price', 'is_popular', 'display_order', 'is_active')
    list_display_links = ('id', 'name',)
    list_editable = ('is_popular', 'display_order', 'is_active')
    inlines = [PackageFeatureInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'tagline', 'price', 'description', 'interval', 'is_active')
        }),
        ('Discount', {
            'fields': ('discount', 'discount_price')
        }),
        ('CMS Settings', {
            'fields': ('is_popular', 'display_order', 'border_color', 'button_color', 'button_text_color'),
            'description': 'Customize the appearance of this package in the pricing section'
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


@admin.register(PackageFeature)
class PackageFeatureAdmin(ModelAdmin):
    list_display = ('package', 'feature_text', 'is_included', 'order')
    list_filter = ('package', 'is_included')
    list_editable = ('order', 'is_included')
    search_fields = ('feature_text', 'package__name')


@admin.register(PricingSection)
class PricingSectionAdmin(ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'subtitle', 'is_active')
        }),
        ('Colors & Styling', {
            'fields': ('background_color', 'text_color', 'popular_badge_text', 'popular_badge_color')
        }),
        ('Button Text', {
            'fields': ('free_plan_button_text', 'paid_plan_button_text')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one pricing section
        return not PricingSection.objects.exists()


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