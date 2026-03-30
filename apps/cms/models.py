from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Page(models.Model):
    class Type(models.TextChoices):
        PRIVACY_POLICY = 'privacy_policy', 'Privacy Policy'
        TERMS_AND_CONDITIONS = 'terms_and_conditions', 'Terms and Conditions'
        COOKIE_POLICY = 'cookie_policy', 'Cookie Policy'
        IMPRINT = 'imprint', 'Imprint'

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    type = models.CharField(max_length=50, choices=Type.choices)
    status = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"


class HeroSection(models.Model):
    """Hero section with main headline and fitness goals"""
    heading = models.CharField(max_length=255, default="What fitness goal do you need to achieve?")
    sub_heading = models.TextField(blank=True, null=True)
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional description text below the heading"
    )
    background_image = models.ImageField(
        upload_to='cms/hero/', 
        blank=True, 
        null=True,
        help_text="Background image for hero section"
    )
    status = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.heading

    class Meta:
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Sections"
        ordering = ['order']


class FitnessGoal(models.Model):
    """Individual fitness goals displayed in the hero section"""
    hero_section = models.ForeignKey(
        HeroSection, 
        on_delete=models.CASCADE, 
        related_name='goals'
    )
    goal_text = models.CharField(max_length=255)
    icon = models.ImageField(
        upload_to='cms/goals/', 
        blank=True, 
        null=True,
        help_text="Icon for this goal"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.goal_text

    class Meta:
        verbose_name = "Fitness Goal"
        verbose_name_plural = "Fitness Goals"
        ordering = ['order']


class SuccessStoriesSection(models.Model):
    """Success Stories section heading"""
    heading = models.CharField(max_length=255, default="Success Stories")
    sub_heading = models.TextField(
        default="Join thousands of others who have made their goals with 3rd+ months of personalized guidance, improved well-being!"
    )
    background_color = models.CharField(
        max_length=50, 
        default="#000000",
        help_text="Background color in hex format"
    )
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.heading

    class Meta:
        verbose_name = "Success Stories Section"
        verbose_name_plural = "Success Stories Sections"

# Success Stories
class Testimonial(models.Model):
    section = models.ForeignKey(
        SuccessStoriesSection, 
        on_delete=models.CASCADE, 
        related_name='testimonials'
    )
    user_name = models.CharField(max_length=100)
    user_avatar = models.ImageField(upload_to='cms/testimonials/', blank=True, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], default=5.0)
    testimonial_text = models.TextField()
    date = models.DateField(auto_now_add=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_name} - {self.rating}★"

    class Meta:
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        ordering = ['order', '-created_at']


class AICoachSection(models.Model):
    """AI Personal Coach section"""
    badge_text = models.CharField(
        max_length=50, 
        default="NEW FEATURE",
        help_text="Badge text above the heading"
    )
    heading = models.CharField(max_length=255, default="AI Personal Coach")
    description = models.TextField(
        default="Get personalized guidance, motivation, and strategies tailored to your specific goals and challenges."
    )
    button_text = models.CharField(max_length=100, default="Learn how it works")
    button_link = models.CharField(max_length=255, blank=True, null=True)
    preview_image = models.ImageField(
        upload_to='cms/ai_coach/', 
        blank=True, 
        null=True,
        help_text="Preview image/screenshot of the AI coach interface"
    )
    background_color = models.CharField(
        max_length=50, 
        default="#000000",
        help_text="Background color in hex format"
    )
    order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.heading

    class Meta:
        verbose_name = "AI Coach Section"
        verbose_name_plural = "AI Coach Sections"
        ordering = ['order']


class FeatureSection(models.Model):
    """Generic feature section for additional content"""
    section_name = models.CharField(max_length=255)
    heading = models.CharField(max_length=255)
    sub_heading = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='cms/features/', 
        blank=True, 
        null=True
    )
    button_text = models.CharField(max_length=100, blank=True, null=True)
    button_link = models.CharField(max_length=255, blank=True, null=True)
    background_color = models.CharField(
        max_length=50, 
        default="#FFFFFF",
        help_text="Background color in hex format"
    )
    order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.section_name

    class Meta:
        verbose_name = "Feature Section"
        verbose_name_plural = "Feature Sections"
        ordering = ['order']


class CTASection(models.Model):
    """Call to Action section"""
    heading = models.CharField(
        max_length=255,
        default="Create AI-powered solutions people genuinely want to use"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description text below the heading"
    )
    button_text = models.CharField(max_length=100, default="Start Free Trial")
    button_link = models.CharField(max_length=255, blank=True, null=True)
    background_color = models.CharField(
        max_length=50, 
        default="#000000",
        help_text="Background color in hex format"
    )
    button_color = models.CharField(
        max_length=50, 
        default="#CCFF00",
        help_text="Button color in hex format"
    )
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.heading

    class Meta:
        verbose_name = "CTA Section"
        verbose_name_plural = "CTA Sections"


class FooterLink(models.Model):
    """Footer navigation links"""
    CATEGORY_CHOICES = [
        ('product', 'Product'),
        ('company', 'Company'),
        ('legal', 'Legal'),
        ('social', 'Social Media'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    icon = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Icon class or image URL"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category} - {self.title}"

    class Meta:
        verbose_name = "Footer Link"
        verbose_name_plural = "Footer Links"
        ordering = ['category', 'order']

# Social Media Links
class SocialMediaLink(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('discord', 'Discord'),
        ('threads', 'Threads'),
        ('other', 'Other'),
    ]
    
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    url = models.CharField(max_length=255)
    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Icon class or Font Awesome class"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.platform

    class Meta:
        verbose_name = "Social Media Link"
        verbose_name_plural = "Social Media Links"
        ordering = ['order']

# FAQs
class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Category for grouping FAQs"
    )
    order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['order']


class WebsiteContentManager(models.Model):
    """
    Master Content Manager - Single entry point for managing all website content
    This is a singleton model with only one instance
    """
    site_name = models.CharField(max_length=255, default="STRENNO Fitness Platform")
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Website Content Manager - {self.site_name}"
    
    class Meta:
        verbose_name = "🎯 Website Content Manager (ALL-IN-ONE)"
        verbose_name_plural = "🎯 Website Content Manager (ALL-IN-ONE)"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        if not self.pk and WebsiteContentManager.objects.exists():
            return WebsiteContentManager.objects.first()
        return super().save(*args, **kwargs)

# Contact
class ContactInfo(models.Model):
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Contact Information"

    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"

# Privacy & Terms
class LegalDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms and Conditions'),
    ]
    type = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES, unique=True)
    version = models.CharField(max_length=20, default="1.0")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} (v{self.version})"
    
    def increment_version(self, major=False):
        try:
            parts = self.version.split('.')
            if major:
                # Increment major version and reset minor
                parts[0] = str(int(parts[0]) + 1)
                if len(parts) > 1:
                    parts[1] = '0'
            else:
                # Increment minor version
                if len(parts) == 1:
                    parts.append('1')
                else:
                    parts[1] = str(int(parts[1]) + 1)
            self.version = '.'.join(parts)
        except (ValueError, IndexError):
            # If version format is invalid, reset to 1.0
            self.version = "1.0"
    
    def save(self, *args, **kwargs):
        # Auto-increment version if content changed (and not a new instance)
        if self.pk:
            try:
                old_instance = LegalDocument.objects.get(pk=self.pk)
                if old_instance.content != self.content:
                    # Content changed, increment minor version
                    self.increment_version(major=False)
            except LegalDocument.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Legal Document"
        verbose_name_plural = "Legal Documents"
