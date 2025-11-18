from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model."""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user_message', 'ai_message', 'workout', 'diet', 'summary', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession model."""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'created_at', 'updated_at', 'messages', 'message_count']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request."""
    session_id = serializers.UUIDField(required=False, allow_null=True)
    user_input = serializers.CharField(required=True, allow_blank=False)
    
    def validate_user_input(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("User input cannot be empty.")
        return value.strip()


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response."""
    session_id = serializers.UUIDField()
    response = serializers.DictField()
    
    def to_representation(self, instance):
        return {
            'session_id': str(instance.get('session_id')),
            'response': {
                'message': instance.get('message', ''),
                'workout': instance.get('workout', []),
                'diet': instance.get('diet', []),
                'summary': instance.get('summary', '')
            }
        }
