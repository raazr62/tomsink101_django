from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import WorkoutPlan, Exercise, DietPlan, Meal, DailyProgress, WorkoutReview


class ExerciseInline(TabularInline):
    model = Exercise
    extra = 0
    fields = ('name', 'sets', 'reps', 'description', 'pro_tips', 'completed_sets', 'status', 'order')


class MealInline(TabularInline):
    model = Meal
    extra = 0
    fields = ('meal_type', 'title', 'calories', 'protein', 'carbs', 'fats', 'status', 'order')


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(ModelAdmin):
    list_display = ('name', 'user', 'status', 'progress_percentage', 'total_exercises', 'start_date', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('name', 'user__email', 'summary')
    readonly_fields = ('id', 'progress_percentage', 'start_date', 'total_exercises', 'completed_exercises', 'created_at', 'updated_at')
    inlines = [ExerciseInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'summary', 'chat_session')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_percentage', 'total_exercises', 'completed_exercises')
        }),
        ('Dates', {
            'fields': ('start_date', 'target_completion_date', 'created_at', 'updated_at')
        }),
    )


@admin.register(Exercise)
class ExerciseAdmin(ModelAdmin):
    list_display = ('name', 'workout_plan', 'sets', 'reps', 'weight', 'completed_sets', 'status', 'exercise_type', 'date')
    list_filter = ('status', 'weight', 'name', 'created_at', 'exercise_type')
    search_fields = ('id', 'name', 'description', 'workout_plan__name', 'workout_plan__user__email', 'exercise_type')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DietPlan)
class DietPlanAdmin(ModelAdmin):
    list_display = ('name', 'user', 'status', 'total_meals', 'total_daily_calories', 'start_date', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('name', 'user__email', 'summary')
    readonly_fields = ('id', 'total_meals', 'total_daily_calories', 'total_daily_protein', 'total_daily_carbs', 'total_daily_fats', 'created_at', 'updated_at')
    inlines = [MealInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'summary', 'chat_session')
        }),
        ('Status & Nutrition', {
            'fields': ('status', 'total_meals', 'total_daily_calories', 'total_daily_protein', 'total_daily_carbs', 'total_daily_fats')
        }),
        ('Dates', {
            'fields': ('target_completion_date', 'created_at', 'updated_at')
        }),
    )


@admin.register(Meal)
class MealAdmin(ModelAdmin):
    list_display = ('title', 'meal_type', 'diet_plan', 'status', 'calories', 'protein', 'carbs', 'fats', 'status', 'date')
    list_filter = ('meal_type', 'status', 'created_at', 'date')
    search_fields = ('id', 'title', 'diet_plan__name', 'diet_plan__user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DailyProgress)
class DailyProgressAdmin(ModelAdmin):
    list_display = ('user', 'date', 'workout_plan', 'diet_plan', 'exercises_completed', 'meals_completed')
    list_filter = ('date', 'user')
    search_fields = ('user__email', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(WorkoutReview)
class WorkoutReviewAdmin(ModelAdmin):
    list_display = ('workout_plan', 'user', 'difficulty', 'satisfaction', 'created_at')
    list_filter = ('difficulty', 'satisfaction', 'target_hit', 'created_at')
    search_fields = ('workout_plan__name', 'user__email', 'feedback')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Workout Plan & User', {
            'fields': ('id', 'workout_plan', 'user')
        }),
        ('Completed Reps', {
            'fields': ('reps_completed',)
        }),
        ('Review Ratings', {
            'fields': ('difficulty', 'target_hit', 'energy_level', 'body_feeling', 'satisfaction')
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
