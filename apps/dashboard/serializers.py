from rest_framework import serializers
from .models import (
FitnessGoal, Workout, WeeklyStats, NutritionPlan, CoachInsight, 
BodyWeightEntry, AchievementDefinition, UserAchievement

)
from apps.users.models import Profile
from datetime import timedelta
from django.utils import timezone
from apps.users.helpers import get_cloudinary_url


class FitnessGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = FitnessGoal
        fields = [
            'id', 'title', 'total_weeks', 'current_week', 'progress_percentage', 
            'start_date', 'end_date', 'is_active', 'created_at'
            ]


class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            'id', 'title', 'workout_type', 'day', 'description', 'exercises_count', 
            'focus_area', 'scheduled_date', 'is_completed', 'completed_at', 
            'duration_minutes', 'calories_burned'
            ]


class WeeklyStatsSerializer(serializers.ModelSerializer):
    workout_percentage = serializers.IntegerField(read_only=True)
    calories_comparison = serializers.SerializerMethodField()
    bodyweight_comparison = serializers.SerializerMethodField()
    workout_minutes_comparison = serializers.SerializerMethodField()
    workouts_comparison = serializers.SerializerMethodField()
    
    class Meta:
        model = WeeklyStats
        fields = [
            'id', 'week_start_date', 'week_end_date', 'workouts_completed', 
            'workouts_target', 'workout_percentage', 'nutrition_score', 
            'overall_streak', 'success_rate', 'calories_burned', 'calories_target',
            'calories_comparison', 'bodyweight_kg', 'bodyweight_target_kg',
            'bodyweight_comparison', 'workout_minutes', 'workout_minutes_target',
            'workout_minutes_comparison', 'workouts_comparison'
            ]

    def get_calories_comparison(self, obj):
        if obj.calories_target == 0:
            return {'difference': 0, 'is_above_target': False}
        difference = obj.calories_burned - obj.calories_target
        return {
            'difference': abs(difference),
            'is_above_target': difference > 0
        }

    def get_bodyweight_comparison(self, obj):
        if not obj.bodyweight_kg or not obj.bodyweight_target_kg:
            return {'difference': 0, 'is_below_target': False}
        difference = float(obj.bodyweight_target_kg) - float(obj.bodyweight_kg)
        return {
            'difference': abs(difference),
            'is_below_target': difference > 0
        }

    def get_workout_minutes_comparison(self, obj):
        if obj.workout_minutes_target == 0:
            return {'difference': 0, 'is_above_target': False}
        difference = obj.workout_minutes - obj.workout_minutes_target
        return {
            'difference': abs(difference),
            'is_above_target': difference > 0
        }

    def get_workouts_comparison(self, obj):
        if obj.workouts_target == 0:
            return {'difference': 0, 'is_above_target': False}
        difference = obj.workouts_completed - obj.workouts_target
        return {
            'difference': abs(difference),
            'is_above_target': difference > 0
        }


class NutritionPlanSerializer(serializers.ModelSerializer):
    protein_difference = serializers.IntegerField(read_only=True)
    calories_difference = serializers.IntegerField(read_only=True)
    fat_difference = serializers.IntegerField(read_only=True)
    carbs_difference = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = NutritionPlan
        fields = [
            'id', 'date', 'protein_g', 'protein_target_g', 'protein_difference',
            'calories', 'calories_target', 'calories_difference',
            'fat_g', 'fat_target_g', 'fat_difference',
            'carbs_g', 'carbs_target_g', 'carbs_difference'
            ]


class CoachInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachInsight
        fields = ['id', 'message', 'insight_type', 'is_read', 'created_at']


class DashboardSerializer(serializers.Serializer):
    """Main dashboard data serializer"""
    user_name = serializers.CharField()
    fitness_goal = FitnessGoalSerializer()
    today_workout = WorkoutSerializer(allow_null=True)
    current_week_stats = WeeklyStatsSerializer()
    today_nutrition = NutritionPlanSerializer()
    latest_coach_insight = CoachInsightSerializer(allow_null=True)
    motivational_quote = serializers.CharField()

# Daily Nutrition Plan
class NutritionPlanSerializer(serializers.Serializer):
    protein = serializers.DictField()
    calories = serializers.DictField()
    carbs = serializers.DictField()
    fats = serializers.DictField()

# BodyWeight Post
class BodyWeightPostSerializer(serializers.ModelSerializer):
    days_until_next = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = BodyWeightEntry
        fields = ['id', 'weight_kg', 'days_until_next']
    
    def get_days_until_next(self, obj):
        
        next_allowed_date = obj.created_at + timedelta(days=15)
        days_left = (next_allowed_date.date() - timezone.now().date()).days
        return max(0, days_left)

# BodyWeight Get
class BodyWeightGetSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.DecimalField(source='weight_kg', max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = BodyWeightEntry
        fields = ['date', 'value']
    
    def get_date(self, obj):
        return obj.created_at.strftime('%b %d').replace(' 0', ' ').strip()

# Achievement Definition
class AchievementDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AchievementDefinition
        fields = [
            'id', 'icon', 'title', 'description', 'target_value', 'order' 
            ]
        
        def get_icon(self, obj):
            return get_cloudinary_url(obj.icon)

# User Achievement
class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementDefinitionSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement', 'period_start', 'actual_value', 'earned_at'
            ]