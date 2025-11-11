from django.db import models
from apps.users.models import User


class NotificationPreference(models.Model):
    """
    User notification preferences model.
    Allows users to control which types of notifications they want to receive.
    Each user has one NotificationPreference record (one-to-one relationship).
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences',
        help_text="User associated with these notification preferences"
    )
    
    # Notification types from the image
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive notifications via email"
    )
    
    daily_checkin_reminders = models.BooleanField(
        default=True,
        help_text="Receive daily check-in reminder notifications"
    )
    
    milestone_achievements = models.BooleanField(
        default=True,
        help_text="Receive notifications about milestone achievements"
    )
    
    ai_insights_and_tips = models.BooleanField(
        default=True,
        help_text="Receive AI-generated insights and tips"
    )
    
    push_notifications = models.BooleanField(
        default=True,
        help_text="Receive push notifications on mobile/web"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Notification Preferences for {self.user.email}"
    
    def enable_all(self):
        """Enable all notification types"""
        self.email_notifications = True
        self.daily_checkin_reminders = True
        self.milestone_achievements = True
        self.ai_insights_and_tips = True
        self.push_notifications = True
        self.save()
    
    def disable_all(self):
        """Disable all notification types"""
        self.email_notifications = False
        self.daily_checkin_reminders = False
        self.milestone_achievements = False
        self.ai_insights_and_tips = False
        self.push_notifications = False
        self.save()
