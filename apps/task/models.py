from django.db import models
from django.conf import settings
import uuid
from cloudinary.models import CloudinaryField

# Workout Plan
class WorkoutPlan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_plans')
    chat_session = models.ForeignKey('manageai.ChatSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='workout_plans')
    name = models.CharField(max_length=255, default='My Workout Plan', null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    target_completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Workout Plan'
        verbose_name_plural = 'Workout Plans'
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    @property
    def total_exercises(self):
        return self.exercises.count()
    
    @property
    def completed_exercises(self):
        return self.exercises.filter(status='completed').count()
    
    @property
    def progress_percentage(self):
        total = self.total_exercises
        if total == 0:
            return 0
        return round((self.completed_exercises / total) * 100, 2)

# Exercise
class Exercise(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    WORKOUT_TYPE_CHOICES = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('mobility', 'Mobility'),
        ('hiit', 'HIIT'),
        ('core', 'Core'),
        ('full_body', 'Full Body'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=255, null=True, blank=True)
    exercise_type = models.CharField(max_length=100, choices=WORKOUT_TYPE_CHOICES, null=True, blank=True)
    date = models.DateField(null=True, blank=True)  # Date for this exercise
    sets = models.IntegerField(default=3)
    reps = models.CharField(max_length=50, null=True, blank=True)  # Can be "10-12" or "30 seconds"
    weight = models.CharField(max_length=50, blank=True, default='')  # Weight used (e.g., "10-15 kg" or empty for bodyweight)
    description = models.TextField(blank=True, null=True)  # Detailed explanation of the exercise
    pro_tips = models.JSONField(blank=True, null=True, default=list)  # Array of pro tips for the exercise
    completed_sets = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Exercise'
        verbose_name_plural = 'Exercises'
    
    def __str__(self):
        return f"{self.name} - {self.sets} sets x {self.reps}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def completion_percentage(self):
        if self.sets == 0:
            return 0
        return round((self.completed_sets / self.sets) * 100, 2)


# Chat messages tied to a specific exercise
class ExerciseChatMessage(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exercise_chats')
    user_message = models.TextField()
    ai_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Exercise Chat Message'
        verbose_name_plural = 'Exercise Chat Messages'

    def __str__(self):
        return f"Chat for {self.exercise.name} by {self.user.email} at {self.created_at}"    


# Diet Plan
class DietPlan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diet_plans')
    chat_session = models.ForeignKey('manageai.ChatSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='diet_plans')
    name = models.CharField(max_length=255, default='My Diet Plan')
    summary = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField(auto_now_add=True)
    target_completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Diet Plan'
        verbose_name_plural = 'Diet Plans'
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    @property
    def total_meals(self):
        return self.meals.count()
    
    @property
    def total_daily_calories(self):
        return sum(meal.calories for meal in self.meals.all())
    
    @property
    def total_daily_protein(self):
        return sum(meal.protein for meal in self.meals.all())
    
    @property
    def total_daily_carbs(self):
        return sum(meal.carbs for meal in self.meals.all())
    
    @property
    def total_daily_fats(self):
        return sum(meal.fats for meal in self.meals.all())

# Meal
class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snack', 'Snack'),
        ('dinner', 'Dinner'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('replaced', 'Replaced'),
        ('skipped', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='meals')
    date = models.DateField(null=True, blank=True)  # Date for this meal
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    items = models.JSONField()  # List of food items
    photo = CloudinaryField('meal_photo', blank=True, null=True)
    calories = models.IntegerField(default=0)
    protein = models.IntegerField(default=0)
    carbs = models.IntegerField(default=0)
    fats = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Meal'
        verbose_name_plural = 'Meals'
    
    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.title}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'



class DailyProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_progress'
    )
    date = models.DateField()
    workout_plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='daily_progress'
    )
    diet_plan = models.ForeignKey(
        DietPlan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='daily_progress'
    )
    exercises_completed = models.IntegerField(default=0)
    meals_completed = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Daily Progress'
        verbose_name_plural = 'Daily Progress'
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"


class WorkoutReview(models.Model):
    """Model to store user reviews and feedback for completed workout plans."""
    DIFFICULTY_CHOICES = [
        ('very_easy', 'Very Easy'),
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('tough', 'Tough'),
        ('very_tough', 'Very Tough'),
    ]
    
    TARGET_HIT_CHOICES = [
        ('not_at_all', 'Not at All'),
        ('slightly', 'Slightly'),
        ('moderately', 'Moderately'),
        ('well', 'Well'),
        ('very_well', 'Very Well'),
    ]
    
    ENERGY_LEVEL_CHOICES = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    BODY_FEELING_CHOICES = [
        ('very_poor', 'Very Poor'),
        ('poor', 'Poor'),
        ('okay', 'Okay'),
        ('good', 'Good'),
        ('excellent', 'Excellent'),
    ]
    
    SATISFACTION_CHOICES = [
        ('very_dissatisfied', 'Very Dissatisfied'),
        ('dissatisfied', 'Dissatisfied'),
        ('neutral', 'Neutral'),
        ('satisfied', 'Satisfied'),
        ('very_satisfied', 'Very Satisfied'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workout_plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workout_reviews'
    )
    
    # Review Questions
    reps_completed = models.CharField(max_length=50, blank=True)  # "How many reps did you complete on average?"
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)  # Q1: How tough was today's workout?
    target_hit = models.CharField(max_length=20, choices=TARGET_HIT_CHOICES)  # Q2: How well did you hit the targets?
    energy_level = models.CharField(max_length=20, choices=ENERGY_LEVEL_CHOICES)  # Q3: Energy level during workout
    body_feeling = models.CharField(max_length=20, choices=BODY_FEELING_CHOICES)  # Q4: How's your body feeling?
    satisfaction = models.CharField(max_length=20, choices=SATISFACTION_CHOICES)  # Q5: Satisfaction level
    
    feedback = models.TextField(blank=True)  # Additional feedback or comments
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Workout Review'
        verbose_name_plural = 'Workout Reviews'
        unique_together = ['workout_plan', 'user']  # One review per workout plan per user
    
    def __str__(self):
        return f"Review for {self.workout_plan.name} by {self.user.email}"
