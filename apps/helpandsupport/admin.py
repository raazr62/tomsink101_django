from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import ContactSupport, LegalDocument, SupportTicket


@admin.register(ContactSupport)
class ContactSupportAdmin(ModelAdmin):
    """
    Admin interface for ContactSupport model.
    Singleton pattern - only one instance allowed.
    """
    list_display = [
        'support_email',
        'support_phone_display',
        'average_response_time',
        'is_active_badge',
        'updated_at',
    ]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('support_email', 'support_phone', 'support_phone_display')
        }),
        ('Response Time', {
            'fields': ('average_response_time',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        # Only allow adding if no instance exists
        return not ContactSupport.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion to maintain singleton
        return False


@admin.register(LegalDocument)
class LegalDocumentAdmin(ModelAdmin):
    """
    Admin interface for LegalDocument model.
    """
    list_display = [
        'title',
        'document_type',
        'version',
        'effective_date',
        'is_active_badge',
        'order',
        'updated_at',
    ]
    
    list_filter = [
        'document_type',
        'is_active',
        'effective_date',
    ]
    
    search_fields = ['title', 'content', 'slug']
    
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'document_type', 'slug', 'version')
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'Full content of the legal document (HTML supported)'
        }),
        ('Settings', {
            'fields': ('effective_date', 'is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'


@admin.register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    """
    Admin interface for SupportTicket model.
    """
    list_display = [
        'ticket_number',
        'subject',
        'email',
        'status_badge',
        'priority_badge',
        'created_at',
        'updated_at',
    ]
    
    list_filter = [
        'status',
        'priority',
        'created_at',
        'resolved_at',
    ]
    
    search_fields = [
        'ticket_number',
        'subject',
        'email',
        'message',
        'user__email',
    ]
    
    readonly_fields = [
        'ticket_number',
        'user',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'user', 'email', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'resolved_at')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'description': 'Internal notes (not visible to user)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_closed']
    
    def status_badge(self, obj):
        colors = {
            'open': 'orange',
            'in_progress': 'blue',
            'waiting_for_user': 'purple',
            'resolved': 'green',
            'closed': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'urgent': 'darkred',
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{count} ticket(s) marked as resolved.')
    mark_as_resolved.short_description = "Mark selected tickets as resolved"
    
    def mark_as_in_progress(self, request, queryset):
        count = queryset.update(status='in_progress')
        self.message_user(request, f'{count} ticket(s) marked as in progress.')
    mark_as_in_progress.short_description = "Mark selected tickets as in progress"
    
    def mark_as_closed(self, request, queryset):
        count = queryset.update(status='closed')
        self.message_user(request, f'{count} ticket(s) marked as closed.')
    mark_as_closed.short_description = "Mark selected tickets as closed"
