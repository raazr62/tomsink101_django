from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import ChatSession, ChatMessage


class ChatMessageInline(TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('id', 'user_message', 'ai_message', 'workout', 'diet', 'summary', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'message_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('id', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [ChatMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(ModelAdmin):
    list_display = ('id', 'session', 'user_message_preview', 'ai_message_preview', 'created_at')
    list_filter = ('created_at', 'session__user')
    search_fields = ('user_message', 'ai_message', 'session__id')
    readonly_fields = ('id', 'created_at')

    def user_message_preview(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    user_message_preview.short_description = 'User Message'

    def ai_message_preview(self, obj):
        return obj.ai_message[:50] + '...' if len(obj.ai_message) > 50 else obj.ai_message
    ai_message_preview.short_description = 'AI Message'
