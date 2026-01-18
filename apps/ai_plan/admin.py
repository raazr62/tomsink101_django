from django.contrib import admin
from .models import AIPlanSession, AIPlanConversation


class AIPlanConversationInline(admin.TabularInline):
    """Inline admin for conversations within a session."""

    model = AIPlanConversation
    extra = 0
    readonly_fields = ["id", "created_at", "updated_at"]
    fields = ["user_message", "ai_message", "summary", "created_at"]
    can_delete = True
    show_change_link = True
    ordering = ["-created_at"]


@admin.register(AIPlanSession)
class AIPlanSessionAdmin(admin.ModelAdmin):
    """Admin interface for AI Plan Sessions."""

    list_display = ["id", "user", "conversation_count", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["id", "created_at", "updated_at", "conversation_count"]
    inlines = [AIPlanConversationInline]

    def conversation_count(self, obj):
        return obj.conversation_count

    conversation_count.short_description = "Conversations"


@admin.register(AIPlanConversation)
class AIPlanConversationAdmin(admin.ModelAdmin):
    """Admin interface for AI Plan Conversations."""

    list_display = ["id", "session", "user_message_preview", "created_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user_message", "ai_message", "summary"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_select_related = ["session", "session__user"]

    fieldsets = [
        ("Session Information", {"fields": ["id", "session"]}),
        ("Conversation", {"fields": ["user_message", "ai_message", "summary"]}),
        ("Plans", {"fields": ["workout", "diet"], "classes": ["collapse"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]

    def user_message_preview(self, obj):
        """Display first 50 characters of user message."""
        return (
            obj.user_message[:50] + "..."
            if len(obj.user_message) > 50
            else obj.user_message
        )

    user_message_preview.short_description = "User Message"
