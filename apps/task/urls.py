from django.urls import path
from .views import (
    ReplaceMealView,
    WorkoutPlanListView,
    WorkoutPlanDetailView,
    ExerciseUpdateView,
    DietPlanListView,
    DietPlanDetailView,
    MealUpdateView,
    DailyProgressView,
    TaskDashboardView,
    WeeklyStatsView,
    WorkoutCalendarView,
    DailyWorkoutDetailView,
    ExerciseSetToggleView,
    MealToggleView,
    ResetAllTaskDataView,
    WorkoutReviewOptionsView,
    WorkoutReviewView,
)

urlpatterns = [
    # Dashboard
    path('dashboard/', TaskDashboardView.as_view(), name='task-dashboard'),
        
    # Weekly Stats (for top cards in UI)
    path('weekly-stats/', WeeklyStatsView.as_view(), name='weekly-stats'),
    
    # Calendar View (for calendar widget)
    path('calendar/', WorkoutCalendarView.as_view(), name='workout-calendar'),
    
    # Daily Workout Details (for clicking on a specific date)
    path('daily/<str:date>/', DailyWorkoutDetailView.as_view(), name='daily-workout-detail'),
    
    # Workout Plans
    path('workout-plans/', WorkoutPlanListView.as_view(), name='workout-plan-list'),
    path('workout-plans/<uuid:plan_id>/', WorkoutPlanDetailView.as_view(), name='workout-plan-detail'),
    
    # Exercises
    path('exercises/<uuid:exercise_id>/', ExerciseUpdateView.as_view(), name='exercise-update'),
    path('exercises/<uuid:exercise_id>/toggle-set/', ExerciseSetToggleView.as_view(), name='exercise-set-toggle'),
    
    # Diet Plans
    path('diet-plans/', DietPlanListView.as_view(), name='diet-plan-list'),
    path('diet-plans/<uuid:plan_id>/', DietPlanDetailView.as_view(), name='diet-plan-detail'),
    
    # Meals
    path('meals/<uuid:meal_id>/', MealUpdateView.as_view(), name='meal-update'),
    path('meals/<uuid:meal_id>/toggle/', MealToggleView.as_view(), name='meal-toggle'),
    
    # Replace Meal
    path('replace-meal/<uuid:meal_id>/', ReplaceMealView.as_view(), name='replace-meal'),

    # Daily Progress
    path('progress/', DailyProgressView.as_view(), name='daily-progress'),
    
    # Reset All Task Data
    path('reset/', ResetAllTaskDataView.as_view(), name='reset-all-task-data'),
    
    # Workout Reviews
    path('review/options/', WorkoutReviewOptionsView.as_view(), name='workout-review-options'),
    path('workout-plans/<uuid:plan_id>/review/', WorkoutReviewView.as_view(), name='workout-review'),
]
