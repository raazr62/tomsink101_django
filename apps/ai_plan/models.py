import uuid
from django.db import models
from django.conf import settings


class AIPlanSession(models.Model):
    """Stores a single AI Plan session for each user.
    Each user has exactly one active session for continuity.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_plan_session",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_plan_sessions"
        ordering = ["-updated_at"]
        verbose_name = "AI Plan Session"
        verbose_name_plural = "AI Plan Sessions"

    def __str__(self):
        return f"AI Plan Session for {self.user.email}"

    @property
    def conversation_count(self):
        """Returns the number of conversations in this session."""
        return self.conversations.count()

    @property
    def last_conversation(self):
        """Returns the most recent conversation."""
        return self.conversations.first()


class AIPlanConversation(models.Model):
    """Stores individual conversation entries within a session.
    Each entry contains user input, AI response, and optional workout/diet data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AIPlanSession, on_delete=models.CASCADE, related_name="conversations"
    )
    user_message = models.TextField(help_text="User's input/question")
    ai_message = models.TextField(help_text="AI's response message")
    summary = models.TextField(
        blank=True, null=True, help_text="Updated user profile summary"
    )
    workout = models.JSONField(
        default=list, blank=True, help_text="Workout plan data in JSON format"
    )
    diet = models.JSONField(
        default=list, blank=True, help_text="Diet plan data in JSON format"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_plan_conversations"
        ordering = ["-created_at"]
        verbose_name = "AI Plan Conversation"
        verbose_name_plural = "AI Plan Conversations"

    def __str__(self):
        return f"Conversation {self.id} - {self.session.user.email}"
