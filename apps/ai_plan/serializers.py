from rest_framework import serializers
from .models import AIPlanSession, AIPlanConversation


class WorkoutExerciseSerializer(serializers.Serializer):
    """Serializer for individual exercise in workout plan."""

    name = serializers.CharField()
    sets = serializers.IntegerField(required=False)
    reps = serializers.CharField(required=False)
    weight = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False)
    pro_tips = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )


class WorkoutDaySerializer(serializers.Serializer):
    """Serializer for a day's workout plan."""

    date = serializers.DateField(required=False)
    exercise = serializers.ListField(
        child=WorkoutExerciseSerializer(), required=False, default=list
    )


class MealItemSerializer(serializers.Serializer):
    """Serializer for individual meal in diet plan."""

    meal = serializers.CharField()
    title = serializers.CharField(required=False)
    items = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    nutrients = serializers.DictField(required=False)


class DietDaySerializer(serializers.Serializer):
    """Serializer for a day's diet plan."""

    date = serializers.DateField(required=False)
    foods = serializers.ListField(
        child=MealItemSerializer(), required=False, default=list
    )


class AskRequestSerializer(serializers.Serializer):
    """Serializer for incoming chat requests."""

    user_input = serializers.CharField(
        required=True, help_text="User's question or input"
    )
    summary = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="User profile summary for context",
    )
    workout = serializers.ListField(
        child=WorkoutDaySerializer(),
        required=False,
        default=list,
        help_text="Current workout plan",
    )
    diet = serializers.ListField(
        child=DietDaySerializer(),
        required=False,
        default=list,
        help_text="Current diet plan",
    )


class AskResponseSerializer(serializers.Serializer):
    """Serializer for AI response data."""

    message = serializers.CharField()
    workout = serializers.ListField(child=WorkoutDaySerializer(), default=list)
    diet = serializers.ListField(child=DietDaySerializer(), default=list)
    summary = serializers.CharField(required=False, allow_blank=True)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for complete chat response."""

    session_id = serializers.UUIDField()
    response = AskResponseSerializer()


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversation history."""

    class Meta:
        model = AIPlanConversation
        fields = [
            "id",
            "user_message",
            "ai_message",
            "summary",
            "workout",
            "diet",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for session with nested conversations."""

    conversations = ConversationSerializer(many=True, read_only=True)
    conversation_count = serializers.IntegerField(read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AIPlanSession
        fields = [
            "id",
            "user_email",
            "conversation_count",
            "conversations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
