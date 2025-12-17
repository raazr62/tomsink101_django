import csv
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import PrelaunchUser, PrelaunchReferral
from unfold.admin import ModelAdmin
from django.http import HttpResponse
from django.utils import timezone


@admin.register(PrelaunchUser)
class PrelaunchUserAdmin(ModelAdmin):
    list_display = [
        'name', 
        'email', 
        'referral_code_display', 
        'referred_by_display',
        'referral_count_display',
        'activated',
        'created_at'
    ]
    list_filter = ['activated', 'created_at']
    search_fields = ['name', 'email', 'referral_code', 'referred_by', 'ip_address']
    readonly_fields = [
        'referral_code',
        'referral_link_display',
        'referral_count',
        'ip_address',
        'user_agent',
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('name', 'email', 'activated')
        }),
        ('Referral Information', {
            'fields': ('referral_code', 'referral_link_display', 'referred_by', 'referral_count')
        }),
        ('Fraud Detection', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    # GET Queryset with referral count
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _referral_count=Count('referrals_made')
        )
        return queryset

    # Referral Code
    def referral_code_display(self, obj):
        return format_html(
            '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{}</code>',
            obj.referral_code
        )
    referral_code_display.short_description = 'Referral Code'

    # Referred By
    def referred_by_display(self, obj):
        if obj.referred_by:
            try:
                parent = PrelaunchUser.objects.get(referral_code=obj.referred_by)
                return format_html(
                    '<a href="?referral_code={}">{}</a> ({})',
                    obj.referred_by,
                    parent.name,
                    obj.referred_by
                )
            except PrelaunchUser.DoesNotExist:
                return format_html('<code>{}</code>', obj.referred_by)
        return '-'
    referred_by_display.short_description = 'Referred By'

    # Referral Count with color coding
    def referral_count_display(self, obj):
        count = obj.referral_count
        if count == 0:
            color = '#999'
        elif count < 5:
            color = '#4CAF50'
        elif count < 10:
            color = '#2196F3'
        else:
            color = '#FF9800'
        
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color,
            count
        )
    referral_count_display.short_description = 'Referrals'
    referral_count_display.admin_order_field = '_referral_count'

    # Referral Link
    def referral_link_display(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.referral_link,
            obj.referral_link
        )
    referral_link_display.short_description = 'Referral Link'

    actions = ['activate_users', 'deactivate_users', 'export_csv']

    # Activate Users
    def activate_users(self, request, queryset):
        updated = queryset.update(activated=True)
        self.message_user(request, f'{updated} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'

    # Deactivate Users
    def deactivate_users(self, request, queryset):
        updated = queryset.update(activated=False)
        self.message_user(request, f'{updated} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'

    # Export to CSV
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="prelaunch_users_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Email', 'Referral Code', 'Referred By', 
            'Referral Count', 'Activated', 'IP Address', 'Created At'
        ])
        
        for user in queryset:
            writer.writerow([
                user.name,
                user.email,
                user.referral_code,
                user.referred_by or '',
                user.referral_count,
                'Yes' if user.activated else 'No',
                user.ip_address or '',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_csv.short_description = 'Export selected to CSV'

@admin.register(PrelaunchReferral)
class PrelaunchReferralAdmin(ModelAdmin):
    list_display = [
        'parent_display',
        'child_display',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = [
        'parent_referral_code',
        'child_email',
        'parent_user__name',
        'parent_user__email',
        'child_user__name'
    ]
    readonly_fields = [
        'parent_referral_code',
        'child_email',
        'child_user',
        'parent_user',
        'created_at'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    # Parent Display
    def parent_display(self, obj):
        if obj.parent_user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small><br><code>{}</code>',
                obj.parent_user.name,
                obj.parent_user.email,
                obj.parent_referral_code
            )
        return format_html('<code>{}</code>', obj.parent_referral_code)
    parent_display.short_description = 'Referrer'

    # Child Display
    def child_display(self, obj):
        if obj.child_user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.child_user.name,
                obj.child_email
            )
        return obj.child_email
    child_display.short_description = 'Referred User'

    # Prevent addition
    def has_add_permission(self, request):
        return False
