from rest_framework import serializers
from .models import WorkoutPlan, Exercise, DietPlan, Meal, DailyProgress, WorkoutReview, ExerciseChatMessage
from apps.users.helpers import get_cloudinary_url

class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for Exercise model."""
    completion_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'date', 'sets', 'reps', 'weight', 'description', 'pro_tips', 'completed_sets', 'notes', 'status', 'order', 
                  'completion_percentage', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkoutPlanSerializer(serializers.ModelSerializer):
    """Serializer for WorkoutPlan model."""
    exercises = ExerciseSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    total_exercises = serializers.ReadOnlyField()
    completed_exercises = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkoutPlan
        fields = ['id', 'user', 'chat_session', 'name', 'summary', 'status', 'start_date', 'target_completion_date',
                  'exercises', 'progress_percentage', 'total_exercises', 'completed_exercises',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'chat_session', 'created_at', 'updated_at']


class MealSerializer(serializers.ModelSerializer):
    """Serializer for Meal model."""
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = Meal
        fields = ['id', 'meal_type', 'title', 'items', 'calories', 'protein', 'carbs', 'fats',
                  'notes', 'status', 'order', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DietPlanSerializer(serializers.ModelSerializer):
    """Serializer for DietPlan model."""
    meals = MealSerializer(many=True, read_only=True)
    total_meals = serializers.ReadOnlyField()
    total_daily_calories = serializers.ReadOnlyField()
    total_daily_protein = serializers.ReadOnlyField()
    total_daily_carbs = serializers.ReadOnlyField()
    total_daily_fats = serializers.ReadOnlyField()
    
    class Meta:
        model = DietPlan
        fields = ['id', 'user', 'chat_session', 'name', 'summary', 'status', 'start_date', 'target_completion_date',
                  'meals', 'total_meals', 'total_daily_calories', 'total_daily_protein',
                  'total_daily_carbs', 'total_daily_fats', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'chat_session', 'created_at', 'updated_at']


class DailyProgressSerializer(serializers.ModelSerializer):
    """Serializer for DailyProgress model."""
    
    class Meta:
        model = DailyProgress
        fields = ['id', 'user', 'date', 'workout_plan', 'diet_plan', 'exercises_completed',
                  'meals_completed', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ExerciseUpdateSerializer(serializers.Serializer):
    """Serializer for updating exercise status."""
    completed_sets = serializers.IntegerField(min_value=0, required=False)
    status = serializers.ChoiceField(choices=Exercise.STATUS_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class MealUpdateSerializer(serializers.Serializer):
    """Serializer for updating meal status."""
    status = serializers.ChoiceField(choices=Meal.STATUS_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class WorkoutReviewSerializer(serializers.ModelSerializer):
    """Serializer for Workout Review."""
    workout_plan_name = serializers.CharField(source='workout_plan.name', read_only=True)
    
    class Meta:
        model = WorkoutReview
        fields = [
            'id', 'workout_plan', 'workout_plan_name', 'user', 'reps_completed', 
            'difficulty', 'target_hit', 'energy_level', 'body_feeling', 
            'satisfaction', 'feedback', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class WorkoutReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Workout Review."""
    
    class Meta:
        model = WorkoutReview
        fields = [
            'workout_plan', 'reps_completed', 'difficulty', 'target_hit', 
            'energy_level', 'body_feeling', 'satisfaction', 'feedback'
        ]
    
    def validate_workout_plan(self, value):
        """Ensure the workout plan belongs to the user."""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("This workout plan does not belong to you.")
        return value


class WorkoutReviewOptionsSerializer(serializers.Serializer):
    """Serializer for Workout Review form options."""
    difficulty_options = serializers.ListField(child=serializers.DictField())
    target_hit_options = serializers.ListField(child=serializers.DictField())
    energy_level_options = serializers.ListField(child=serializers.DictField())
    body_feeling_options = serializers.ListField(child=serializers.DictField())


# ---- exercise chat serializers ----
class ExerciseChatRequestSerializer(serializers.Serializer):
    exercise_id = serializers.UUIDField()
    user_input = serializers.CharField()

    def validate_user_input(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("User input cannot be empty.")
        return value.strip()


class ExerciseChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseChatMessage
        fields = ['id', 'exercise', 'user', 'user_message', 'ai_message', 'created_at']
        read_only_fields = ['id', 'exercise', 'user', 'created_at']
    satisfaction_options = serializers.ListField(child=serializers.DictField())

# Replace Meal
class ReplaceMealSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Meal
        fields = [
            'id', 
            'photo',
            'title', 
            'calories', 
            'protein', 
            'carbs', 
            'fats'
        ]
        extra_kwargs = {'photo': {'required': False, 'allow_null': True}}

    def get_photo(self, obj):
        return get_cloudinary_url(obj.photo)