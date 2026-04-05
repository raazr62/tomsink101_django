from rest_framework import serializers
from .models import ChatSession, ChatMessage

# Chat Message
class ChatMessageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user_message', 'ai_message', 'workout', 'diet', 'summary', 'created_at']
        read_only_fields = ['id', 'created_at']

# Chat Session
class ChatSessionSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    workout_plans_count = serializers.SerializerMethodField()
    diet_plans_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'created_at', 'updated_at', 'messages', 'message_count',
                  'workout_plans_count', 'diet_plans_count']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_messages(self, obj):
        # Return only chat messages
        chat_messages = obj.messages.filter(message_type='chat')
        return ChatMessageSerializer(chat_messages, many=True).data
    
    def get_message_count(self, obj):
        return obj.messages.filter(message_type='chat').count()
    
    def get_workout_plans_count(self, obj):
        return obj.workout_plans.count()
    
    def get_diet_plans_count(self, obj):
        return obj.diet_plans.count()

# Chat Session Detail 
class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    workout_plans = serializers.SerializerMethodField()
    diet_plans = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'created_at', 'updated_at', 'messages', 'message_count',
                  'workout_plans', 'diet_plans']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_messages(self, obj):
        # Return only chat messages
        chat_messages = obj.messages.filter(message_type='chat')
        return ChatMessageSerializer(chat_messages, many=True).data
    
    def get_message_count(self, obj):
        return obj.messages.filter(message_type='chat').count()
    
    def get_workout_plans(self, obj):
        from apps.task.serializers import WorkoutPlanSerializer
        plans = obj.workout_plans.all().order_by('-created_at')
        return WorkoutPlanSerializer(plans, many=True).data
    
    def get_diet_plans(self, obj):
        from apps.task.serializers import DietPlanSerializer
        plans = obj.diet_plans.all().order_by('-created_at')
        return DietPlanSerializer(plans, many=True).data

# Chat Request
class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True)
    user_input = serializers.CharField(required=True, allow_blank=False)
    
    def validate_user_input(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("User input cannot be empty.")
        return value.strip()

# Chat Response
class ChatResponseSerializer(serializers.Serializer):
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

# Modify Plan Request
class ModifyPlanRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True)
    workout_plan_id = serializers.UUIDField(required=False, allow_null=True)
    diet_plan_id = serializers.UUIDField(required=False, allow_null=True)
    exercise_id = serializers.UUIDField(required=False, allow_null=True)  # For updating specific exercise
    meal_id = serializers.UUIDField(required=False, allow_null=True)  # For updating specific meal
    modification_request = serializers.CharField(required=True, allow_blank=False)
    
    def validate_modification_request(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Modification request cannot be empty.")
        return value.strip()
    
    def validate(self, data):
        # Allow either plan-level or specific exercise/meal-level updates
        has_plan = data.get('workout_plan_id') or data.get('diet_plan_id')
        has_specific = data.get('exercise_id') or data.get('meal_id')
        
        if not has_plan and not has_specific:
            raise serializers.ValidationError(
                "At least one of: workout_plan_id, diet_plan_id, exercise_id, or meal_id must be provided."
            )
        return data
