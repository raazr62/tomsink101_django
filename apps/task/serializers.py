from rest_framework import serializers
from .models import WorkoutPlan, Exercise, DietPlan, Meal, DailyProgress


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for Exercise model."""
    completion_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'sets', 'reps', 'completed_sets', 'notes', 'status', 'order', 
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
