from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User


class Review(models.Model):
    """
    User feedback/review model
    Stores user feedback with ratings and comments
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        null=True,
        blank=True,
        help_text="User who submitted the review (optional for anonymous reviews)"
    )
    
    # Rating (1-5 stars)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    
    # Feedback text
    feedback_text = models.TextField(
        max_length=500,
        help_text="User feedback, suggestions, or comments (max 500 characters)"
    )
    
    # User info for anonymous submissions
    user_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name for anonymous reviews"
    )
    user_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email for anonymous reviews"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderation
    is_approved = models.BooleanField(
        default=False,
        help_text="Admin approval for displaying on website"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this review on homepage"
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes (not visible to users)"
    )
    
    # Response
    admin_response = models.TextField(
        blank=True,
        null=True,
        help_text="Admin response to the review"
    )
    responded_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When admin responded"
    )
    
    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        user_identifier = self.get_user_identifier()
        return f"{user_identifier} - {self.rating}★ - {self.created_at.strftime('%Y-%m-%d')}"
    
    def get_user_identifier(self):
        """Get user identifier (username or name or email)"""
        if self.user:
            # Check if user has a profile with name
            if hasattr(self.user, 'profile') and self.user.profile.name:
                return self.user.profile.name
            return self.user.email
        elif self.user_name:
            return self.user_name
        elif self.user_email:
            return self.user_email
        return "Anonymous"
    
    @property
    def rating_stars(self):
        """Return star representation of rating"""
        return '⭐' * self.rating
    
    @property
    def feedback_preview(self):
        """Return preview of feedback text"""
        if len(self.feedback_text) > 100:
            return f"{self.feedback_text[:100]}..."
        return self.feedback_text


class ReviewCategory(models.Model):
    """
    Categories for organizing reviews/feedback
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Icon class (e.g., 'fas fa-star')"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Review Category"
        verbose_name_plural = "Review Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class ReviewSettings(models.Model):
    """
    Global settings for review system (Singleton)
    """
    # Display settings
    enable_reviews = models.BooleanField(
        default=True,
        help_text="Enable/disable review submission"
    )
    require_approval = models.BooleanField(
        default=True,
        help_text="Require admin approval before displaying reviews"
    )
    allow_anonymous = models.BooleanField(
        default=True,
        help_text="Allow anonymous reviews without login"
    )
    
    # Form settings
    show_title = models.CharField(
        max_length=255,
        default="Share Your Feedback",
        help_text="Form heading"
    )
    show_subtitle = models.CharField(
        max_length=255,
        default="Help us improve your experience",
        help_text="Form subheading"
    )
    placeholder_text = models.CharField(
        max_length=255,
        default="Share your thoughts, suggestions, or anything else you'd like us to know...",
        help_text="Placeholder text for feedback textarea"
    )
    submit_button_text = models.CharField(
        max_length=100,
        default="Submit Feedback"
    )
    
    # Validation
    min_rating = models.IntegerField(default=1)
    max_rating = models.IntegerField(default=5)
    min_text_length = models.IntegerField(default=10)
    max_text_length = models.IntegerField(default=500)
    
    # Email notifications
    notify_on_new_review = models.BooleanField(
        default=True,
        help_text="Send email to admin on new review"
    )
    notification_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address for notifications"
    )
    
    # Display settings
    show_on_homepage = models.BooleanField(
        default=True,
        help_text="Show review form on homepage"
    )
    reviews_per_page = models.IntegerField(default=10)
    
    # Updated
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Review Settings"
        verbose_name_plural = "Review Settings"
    
    def __str__(self):
        return "Review System Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton)
        if not self.pk and ReviewSettings.objects.exists():
            return ReviewSettings.objects.first()
        return super().save(*args, **kwargs)
