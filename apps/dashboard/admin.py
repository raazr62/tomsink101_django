from django.contrib import admin
from .models import FitnessGoal, Workout, WeeklyStats, NutritionPlan, CoachInsight

# Register your models here.

@admin.register(FitnessGoal)
class FitnessGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'current_week', 'total_weeks', 'progress_percentage', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['progress_percentage', 'created_at', 'updated_at']


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'workout_type', 'day', 'scheduled_date', 'is_completed', 'duration_minutes', 'calories_burned']
    list_filter = ['workout_type', 'is_completed', 'scheduled_date']
    search_fields = ['user__email', 'title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'


@admin.register(WeeklyStats)
class WeeklyStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start_date', 'workouts_completed', 'workout_percentage', 
                    'nutrition_score', 'overall_streak', 'success_rate']
    list_filter = ['week_start_date']
    search_fields = ['user__email']
    readonly_fields = ['workout_percentage', 'created_at', 'updated_at']
    date_hierarchy = 'week_start_date'


@admin.register(NutritionPlan)
class NutritionPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'calories', 'calories_target', 'protein_g', 'fat_g', 'carbs_g']
    list_filter = ['date']
    search_fields = ['user__email']
    readonly_fields = ['protein_difference', 'calories_difference', 'fat_difference', 
                      'carbs_difference', 'created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(CoachInsight)
class CoachInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'is_read', 'created_at']
    list_filter = ['insight_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'message']
    readonly_fields = ['created_at', 'updated_at']

