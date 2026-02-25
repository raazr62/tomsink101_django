from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from apps.users.helpers import preview_image
from django.utils.html import format_html

from .models import (
    BodyWeightEntry, FitnessGoal, Workout, WeeklyStats, 
    NutritionPlan, CoachInsight, AchievementDefinition, UserAchievement
)

@admin.register(FitnessGoal)
class FitnessGoalAdmin(ModelAdmin):
    list_display = ['user', 'title', 'current_week', 'total_weeks', 'progress_percentage', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['progress_percentage', 'created_at', 'updated_at']

@admin.register(Workout)
class WorkoutAdmin(ModelAdmin):
    list_display = ['user', 'title', 'workout_type', 'day', 'scheduled_date', 'is_completed', 'duration_minutes', 'calories_burned']
    list_filter = ['workout_type', 'is_completed', 'scheduled_date']
    search_fields = ['user__email', 'title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'

@admin.register(WeeklyStats)
class WeeklyStatsAdmin(ModelAdmin):
    list_display = ['user', 'week_start_date', 'workouts_completed', 'workout_percentage', 
                    'nutrition_score', 'overall_streak', 'success_rate']
    list_filter = ['week_start_date']
    search_fields = ['user__email']
    readonly_fields = ['workout_percentage', 'created_at', 'updated_at']
    date_hierarchy = 'week_start_date'

@admin.register(NutritionPlan)
class NutritionPlanAdmin(ModelAdmin):
    list_display = ['user', 'date', 'calories', 'calories_target', 'protein_g', 'fat_g', 'carbs_g']
    list_filter = ['date']
    search_fields = ['user__email']
    readonly_fields = ['protein_difference', 'calories_difference', 'fat_difference', 
                    'carbs_difference', 'created_at', 'updated_at']
    date_hierarchy = 'date'

@admin.register(CoachInsight)
class CoachInsightAdmin(ModelAdmin):
    list_display = ['user', 'insight_type', 'is_read', 'created_at']
    list_filter = ['insight_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'message']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BodyWeightEntry)
class BodyWeightEntryAdmin(ModelAdmin):
    list_display = ['user', 'weight_kg', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']

# Admin for Achievements
@admin.register(AchievementDefinition)
class AchievementDefinitionAdmin(ModelAdmin):
    list_display = ['preview_icon', 'title', 'description', 'target_value', 'order']
    list_filter = ['title']
    search_fields = ['title']

    def preview_icon(self, obj):
        if obj.icon:
            url = preview_image(obj.icon)
            return format_html('<img src="{}" style="max-height: 40px; max-width: 30px;" />', url)
        return "No Icon"

# User Achievements
class UserAchievementInline(TabularInline):
    model = UserAchievement
    extra = 0
    readonly_fields = ['period_start', 'actual_value', 'earned_at']

@admin.register(UserAchievement)
class UserAchievementAdmin(ModelAdmin):
    list_display = ['user', 'achievement', 'period_start', 'actual_value', 'earned_at']
    list_filter = ['achievement__title', 'earned_at']
    search_fields = ['user__email', 'achievement__title']
    readonly_fields = ['period_start', 'actual_value', 'earned_at']