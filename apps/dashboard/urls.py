from django.urls import path
from .views import (
    WelcomeView,
    UserWorkoutStatsView,
    NutritionPlanView,
    MyPlanStatsView,
    BodyWeightView,

    
    
    FitnessDashboardView,
    WorkoutListCreateView,
    WorkoutDetailView,
    NutritionUpdateView,
    WeeklyStatsView,
    CoachInsightListView,
    CoachInsightDetailView,
    
)

urlpatterns = [
    # Welcome endpoint
    path('dashboard/welcome/', WelcomeView.as_view(), name='welcome'),
    path('dashboard/workout-stats/', UserWorkoutStatsView.as_view(), name='workout-stats'),
    path("dashboard/daily-nutrition-stats/", NutritionPlanView.as_view(), name="daily-nutrition-plan"),
    path("my-plan/stats/", MyPlanStatsView.as_view(), name="my-plan-stats"),
    path("dashboard/bodyweight/", BodyWeightView.as_view(), name="bodyweight-entry"),








    
    # Main dashboard endpoint
    path('dashboard/', FitnessDashboardView.as_view(), name='fitness-dashboard'),
    
    # Workout endpoints
    path('dashboard/workouts/', WorkoutListCreateView.as_view(), name='workout-list-create'),
    path('dashboard/workouts/<int:pk>/', WorkoutDetailView.as_view(), name='workout-detail'),
    
    # Nutrition endpoints
    path('dashboard/nutrition/', NutritionUpdateView.as_view(), name='nutrition-update'),
    
    # Weekly stats endpoints
    path('dashboard/stats/', WeeklyStatsView.as_view(), name='weekly-stats'),
    
    # Coach insights endpoints
    path('dashboard/insights/', CoachInsightListView.as_view(), name='coach-insights-list'),
    path('dashboard/insights/<int:pk>/', CoachInsightDetailView.as_view(), name='coach-insight-detail'),
]
