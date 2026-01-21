from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class FitnessGoal(models.Model):
    """User's fitness goal tracking (e.g., 12-week program)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fitness_goals')
    title = models.CharField(max_length=200, default="Fitness Journey")
    total_weeks = models.IntegerField(default=12)
    current_week = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.title}"

    @property
    def progress_percentage(self):
        """Calculate progress percentage based on current week"""
        if self.total_weeks == 0:
            return 0
        return int((self.current_week / self.total_weeks) * 100)


class Workout(models.Model):
    """Individual workout sessions"""
    WORKOUT_TYPES = [
        ('upper_body', 'Upper Body Strength'),
        ('lower_body', 'Lower Body Strength'),
        ('cardio', 'Cardio'),
        ('core', 'Core'),
        ('full_body', 'Full Body'),
        ('flexibility', 'Flexibility'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workouts')
    title = models.CharField(max_length=200)
    workout_type = models.CharField(max_length=50, choices=WORKOUT_TYPES)
    day = models.IntegerField(help_text="Day number in the program")
    description = models.TextField(blank=True)
    exercises_count = models.IntegerField(default=8)
    focus_area = models.CharField(max_length=200, blank=True, help_text="e.g., Chest & Back focus")
    scheduled_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=45)
    calories_burned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.title} - Day {self.day}"


class WeeklyStats(models.Model):
    """Weekly fitness statistics"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_stats')
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    
    # Workout stats
    workouts_completed = models.IntegerField(default=0)
    workouts_target = models.IntegerField(default=5)
    
    # Nutrition stats  
    nutrition_score = models.IntegerField(default=0, help_text="Percentage 0-100")
    
    # Streak
    overall_streak = models.IntegerField(default=0, help_text="Consecutive days")
    
    # Success rate
    success_rate = models.IntegerField(default=0, help_text="Percentage 0-100")
    
    # Calories
    calories_burned = models.IntegerField(default=0)
    calories_target = models.IntegerField(default=2000)
    
    # Bodyweight
    bodyweight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bodyweight_target_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Workout time
    workout_minutes = models.IntegerField(default=0)
    workout_minutes_target = models.IntegerField(default=150)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-week_start_date']
        verbose_name_plural = "Weekly Stats"

    def __str__(self):
        return f"{self.user} - Week {self.week_start_date}"

    @property
    def workout_percentage(self):
        if self.workouts_target == 0:
            return 0
        return int((self.workouts_completed / self.workouts_target) * 100)


class NutritionPlan(models.Model):
    """Daily nutrition tracking"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nutrition_plans')
    date = models.DateField()
    
    # Macros consumed
    protein_g = models.IntegerField(default=0)
    calories = models.IntegerField(default=0)
    fat_g = models.IntegerField(default=0)
    carbs_g = models.IntegerField(default=0)
    
    # Targets
    protein_target_g = models.IntegerField(default=140)
    calories_target = models.IntegerField(default=2200)
    fat_target_g = models.IntegerField(default=70)
    carbs_target_g = models.IntegerField(default=300)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user} - {self.date}"

    @property
    def protein_difference(self):
        return self.protein_g - self.protein_target_g

    @property
    def calories_difference(self):
        return self.calories - self.calories_target

    @property
    def fat_difference(self):
        return self.fat_g - self.fat_target_g

    @property
    def carbs_difference(self):
        return self.carbs_g - self.carbs_target_g


class CoachInsight(models.Model):
    """AI-generated or manual coach insights"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coach_insights')
    message = models.TextField()
    insight_type = models.CharField(max_length=50, default='general', 
                                   help_text="e.g., motivation, adjustment, warning")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Insight for {self.user} - {self.created_at.date()}"
