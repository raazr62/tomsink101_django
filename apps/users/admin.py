from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import User, Profile, UserReferral
from django.utils.html import format_html
from django.db.models import Count

@admin.register(User)
class CustomAdminClass(ModelAdmin):
    list_display = ('id', 'email', 'name', 'is_email_verified', 'otp_attempts', 'preview_user_image', 'check_is_superuser')
    list_display_links = ('id', 'email', 'name', 'preview_user_image', 'check_is_superuser')
    search_fields = ('email', 'name')
    list_filter = ('is_email_verified', 'is_active', 'is_superuser')


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(id=1)


    def name(self, obj):
        return obj.profile.name if hasattr(obj, 'profile') else ''


    def preview_user_image(self, obj):
        if obj.profile.avatar:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.profile.avatar.url)
        return "No Image"
    
    def check_is_superuser(self, obj):
        return 'YES' if obj.is_superuser else 'NO'
    
@admin.register(Profile)
class UserProfileAdmin(ModelAdmin):
    list_display = (
        'id', 
        'name', 
        'user', 
        'referral_code_display', 
        'referred_by_display', 
        'referred_users_emails', 
        'avatar_display', 
        'referral_count_display'
        )
    list_display_links = ('id', 'user', 'name')
    search_fields = ('user__email', 'name', 'referral_code', 'referred_by')
    readonly_fields = ('referral_code', 'referral_link_display', 'referral_count')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name', 'avatar', 'dob', 'accepted_terms')
        }),
        ('Referral Information', {
            'fields': ('referral_code', 'referral_link_display', 'referred_by', 'referral_count')
        }),
    )
    ordering = ['-user__created_at']

    # Override get_queryset to annotate referral counts
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _referral_count=Count('referrals_made')
        )
        return queryset
    
    # Referral Code Display
    def referral_code_display(self, obj):
        if obj.referral_code:
            return format_html(
                '<code style=padding: 2px 6px; border-radius: 3px;">{}</code>',
                obj.referral_code
            )
        return '-'
    referral_code_display.short_description = 'Own Referral Code'

    # Referred By email Display
    def referred_by_display(self, obj):
        if obj.referred_by:
            try:
                parent = Profile.objects.get(referral_code=obj.referred_by)
                return format_html(
                    '<a href="?referral_code={}">{}</a>',
                    obj.referred_by,
                    parent.user.email
                )
            except Profile.DoesNotExist:
                return format_html('<code>{}</code>', obj.referred_by)
        return '-'
    referred_by_display.short_description = 'Referred By Code'

    # Referral Count Display with color coding
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
    referral_count_display.short_description = 'Total Referrals'
    referral_count_display.admin_order_field = '_referral_count'

    # Referred Users Emails Display
    def referred_users_emails(self, obj):
        # Try both the relationship and direct query by referral code
        referrals = UserReferral.objects.filter(parent_referral_code=obj.referral_code)
        if not referrals.exists():
            # Fallback to relationship if referral codes don't match
            referrals = obj.referrals_made.all()
        
        if referrals.exists():
            emails = []
            for referral in referrals[:5]:  # Limit to first 5 to avoid too long display
                if referral.child_profile:
                    emails.append(referral.child_profile.user.email)
                else:
                    emails.append(referral.child_email or 'Unknown')
            
            if referrals.count() > 5:
                emails.append(f'... +{referrals.count() - 5} more')
            
            return format_html('<code>{}</small>', ', '.join(emails))
        return '-'
    referred_users_emails.short_description = 'Referred By Emails'

    # Referral Link Display
    def referral_link_display(self, obj):
        if obj.referral_code:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.referral_link,
                obj.referral_link
            )
        return '-'
    referral_link_display.short_description = 'Referral Link'

    # Avatar Display
    def avatar_display(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.avatar.url)
        return "No Image"
    avatar_display.short_description = 'Avatar'

@admin.register(UserReferral)
class UserReferralAdmin(ModelAdmin):
    list_display = [
        'parent_display',
        'child_display',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = [
        'parent_referral_code',
        'child_email',
        'parent_profile__name',
        'parent_profile__user__email',
        'child_profile__name'
    ]
    readonly_fields = [
        'parent_referral_code',
        'child_email',
        'child_profile',
        'parent_profile',
        'created_at'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    # Parent Display
    def parent_display(self, obj):
        if obj.parent_profile:
            return format_html(
                '<strong>{}</strong><br><small>{}</small><br><code>{}</code>',
                obj.parent_profile.name or obj.parent_profile.user.email,
                obj.parent_profile.user.email,
                obj.parent_referral_code
            )
        return format_html('<code>{}</code>', obj.parent_referral_code)
    parent_display.short_description = 'Referrer'

    # Child Display
    def child_display(self, obj):
        if obj.child_profile:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.child_profile.name or obj.child_profile.user.email,
                obj.child_email
            )
        return obj.child_email
    child_display.short_description = 'Referred User'

    # Disable add permission
    def has_add_permission(self, request):
        return False