from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from apps.review.models import Review, ReviewCategory, ReviewSettings
from unfold.admin import ModelAdmin


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    """
    Admin interface for managing reviews/feedback
    """
    list_display = (
        'id', 'user_identifier_display', 'rating_display', 
        'feedback_preview_display', 'created_at', 
        'approval_status', 'featured_status'
    )
    list_display_links = ('id', 'user_identifier_display')
    list_filter = (
        'rating', 'is_approved', 'is_featured', 'created_at'
    )
    search_fields = (
        'feedback_text', 'user_name', 'user_email',
        'user__email', 'user__first_name', 'user__last_name'
    )
    readonly_fields = ('created_at', 'updated_at', 'rating_stars')
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    actions = ['approve_reviews', 'unapprove_reviews', 'feature_reviews', 'unfeature_reviews']
    
    fieldsets = (
        ('⭐ Review Information', {
            'fields': ('rating', 'rating_stars', 'feedback_text')
        }),
        ('👤 User Information', {
            'fields': ('user', 'user_name', 'user_email')
        }),
        ('✅ Moderation', {
            'fields': ('is_approved', 'is_featured', 'admin_notes')
        }),
        ('💬 Admin Response', {
            'fields': ('admin_response', 'responded_at'),
            'classes': ('collapse',)
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_identifier_display(self, obj):
        """Display user identifier with icon"""
        identifier = obj.get_user_identifier()
        if obj.user:
            return format_html(
                '<span style="color: #28a745;">👤 {}</span>',
                identifier
            )
        return format_html(
            '<span style="color: #6c757d;">👤 {} (Guest)</span>',
            identifier
        )
    user_identifier_display.short_description = 'User'
    
    def rating_display(self, obj):
        """Display rating with stars"""
        stars = '⭐' * obj.rating
        return format_html(
            '<span style="font-size: 16px;">{}</span> <small>({})</small>',
            stars, obj.rating
        )
    rating_display.short_description = 'Rating'
    
    def feedback_preview_display(self, obj):
        """Display feedback preview"""
        preview = obj.feedback_preview
        return format_html(
            '<span style="color: #495057;">{}</span>',
            preview
        )
    feedback_preview_display.short_description = 'Feedback'
    
    def approval_status(self, obj):
        """Display approval status with color"""
        if obj.is_approved:
            return format_html(
                '<span style="color: white; background: #28a745; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color: white; background: #ffc107; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⏳ Pending</span>'
        )
    approval_status.short_description = 'Status'
    
    def featured_status(self, obj):
        """Display featured status"""
        if obj.is_featured:
            return format_html(
                '<span style="color: #ffc107; font-size: 18px;">⭐</span>'
            )
        return '-'
    featured_status.short_description = 'Featured'
    
    # Actions
    def approve_reviews(self, request, queryset):
        """Approve selected reviews"""
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} review(s) approved.')
    approve_reviews.short_description = '✓ Approve selected reviews'
    
    def unapprove_reviews(self, request, queryset):
        """Unapprove selected reviews"""
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} review(s) unapproved.')
    unapprove_reviews.short_description = '✗ Unapprove selected reviews'
    
    def feature_reviews(self, request, queryset):
        """Feature selected reviews"""
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} review(s) featured.')
    feature_reviews.short_description = '⭐ Feature selected reviews'
    
    def unfeature_reviews(self, request, queryset):
        """Unfeature selected reviews"""
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} review(s) unfeatured.')
    unfeature_reviews.short_description = '☆ Unfeature selected reviews'


@admin.register(ReviewCategory)
class ReviewCategoryAdmin(ModelAdmin):
    """
    Admin interface for review categories
    """
    list_display = ('id', 'name', 'icon', 'order', 'is_active')
    list_display_links = ('id', 'name')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'icon')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )


@admin.register(ReviewSettings)
class ReviewSettingsAdmin(ModelAdmin):
    """
    Admin interface for review system settings
    """
    fieldsets = (
        ('🔧 System Settings', {
            'fields': ('enable_reviews', 'require_approval', 'allow_anonymous')
        }),
        ('📝 Form Configuration', {
            'fields': (
                'show_title', 'show_subtitle', 'placeholder_text',
                'submit_button_text'
            )
        }),
        ('✅ Validation Rules', {
            'fields': (
                'min_rating', 'max_rating',
                'min_text_length', 'max_text_length'
            )
        }),
        ('📧 Email Notifications', {
            'fields': ('notify_on_new_review', 'notification_email'),
            'classes': ('collapse',)
        }),
        ('🎨 Display Settings', {
            'fields': ('show_on_homepage', 'reviews_per_page'),
            'classes': ('collapse',)
        }),
        ('📅 Last Updated', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not ReviewSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False
