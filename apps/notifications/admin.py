from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    """
    Admin interface for NotificationPreference model.
    """
    list_display = [
        'user_email',
        'email_notifications',
        'daily_checkin_reminders',
        'milestone_achievements',
        'ai_insights_and_tips',
        'push_notifications',
        'updated_at',
    ]
    
    list_filter = [
        'email_notifications',
        'daily_checkin_reminders',
        'milestone_achievements',
        'ai_insights_and_tips',
        'push_notifications',
        'updated_at',
    ]
    
    search_fields = ['user__email']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Notification Settings', {
            'fields': (
                'email_notifications',
                'daily_checkin_reminders',
                'milestone_achievements',
                'ai_insights_and_tips',
                'push_notifications',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    actions = ['enable_all_notifications', 'disable_all_notifications']
    
    def enable_all_notifications(self, request, queryset):
        """Bulk action to enable all notifications for selected users"""
        count = 0
        for preference in queryset:
            preference.enable_all()
            count += 1
        self.message_user(request, f'Enabled all notifications for {count} users.')
    enable_all_notifications.short_description = "Enable all notifications for selected users"
    
    def disable_all_notifications(self, request, queryset):
        """Bulk action to disable all notifications for selected users"""
        count = 0
        for preference in queryset:
            preference.disable_all()
            count += 1
        self.message_user(request, f'Disabled all notifications for {count} users.')
    disable_all_notifications.short_description = "Disable all notifications for selected users"
