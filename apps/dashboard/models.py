from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField

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

# Weekly Fitness Stats
class WeeklyStats(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_stats')
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    calories_burned = models.IntegerField(default=0)
    
    workouts_completed = models.IntegerField(default=0)
    workouts_target = models.IntegerField(default=5)
    nutrition_score = models.IntegerField(default=0, help_text="Percentage 0-100")
    overall_streak = models.IntegerField(default=0, help_text="Consecutive days")
    success_rate = models.IntegerField(default=0, help_text="Percentage 0-100")
    
    calories_target = models.IntegerField(default=2000)
    bodyweight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bodyweight_target_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bodyweight_initial = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coach_insights')
    message = models.TextField()
    insight_type = models.CharField(max_length=50, default='general', help_text="e.g., motivation, adjustment, warning")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Insight for {self.user} - {self.created_at.date()}"

# Body Weight
class BodyWeightEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bodyweight_entries')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'created_at']

    def __str__(self):
        return f"{self.user} - {self.weight_kg}"

# Achievements
class Achievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements', null=True, blank=True)
    total_earned = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.total_earned}"

# Achievement Carts
class AchievementDefinition(models.Model):
    TITLE_CHOICES = [
        ('calorie crusher', 'Calorie Crusher'),
        ('strength master', 'Strength Master'),
        ('marathon runner', 'Marathon Runner'),
        ('active days', 'Active Days'),
        ('workout finisher', 'Workout Finisher'),
        ('perfect week', 'Perfect Week'),
    ]
    
    icon = CloudinaryField('achievement_icon', null=True, blank=True)
    title = models.CharField(max_length=100, choices=TITLE_CHOICES)
    description = models.TextField(null=True, blank=True)
    target_value = models.IntegerField(default=0, null=True, blank=True)
    order = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order']
        verbose_name = "Achievement Input Definition"
        verbose_name_plural = "Achievement Input Definitions"

# User Achievements
class UserAchievement(models.Model):
    STATUS_CHOICES = [
        ('earned', 'Earned'),
        ('in_progress', 'In Progress'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    achievement = models.ForeignKey(AchievementDefinition, on_delete=models.CASCADE)
    period_start = models.DateField(null=True, blank=True) 
    actual_value = models.IntegerField(default=0, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    earned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.achievement.title} - {self.actual_value}"

