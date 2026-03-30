from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

SUBSCRIPTION_TYPE = (
    ('year', 'Yearly'),
    ('month', 'Monthly'),
    ('week', 'Weekly'),
    ('daily', 'Daily')
)

class Package(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True, null=True, help_text='e.g., "Perfect for trying out GoalAI"')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    interval = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPE, default='month')

    stripe_product_id = models.CharField(max_length=100, blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    
    # PayPal IDs
    paypal_product_id = models.CharField(max_length=100, blank=True)
    paypal_plan_id = models.CharField(max_length=100, blank=True)

    discount = models.DecimalField(help_text='Set discount percentages.',max_digits=10, decimal_places=2, default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # CMS fields
    is_popular = models.BooleanField(default=False, help_text='Mark as "Most Popular" plan')
    display_order = models.IntegerField(default=0, help_text='Display order (lower numbers appear first)')
    border_color = models.CharField(max_length=50, default='#4a4a4a', help_text='Card border color (hex)')
    button_color = models.CharField(max_length=50, default='#d4ff00', help_text='Button background color (hex)')
    button_text_color = models.CharField(max_length=50, default='#000000', help_text='Button text color (hex)')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f'{self.name}'
    
    def get_discount_price(self):
        return self.price - (self.price * self.discount / 100)
    
    def save(self, *args, **kwargs):
        if self.discount > 0 and self.discount_price >= 0:
            self.discount_price = self.get_discount_price()
        else:
            self.discount_price = self.price
        super().save(*args, **kwargs)

# User Subscription
class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription_user')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='subscription_package')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('free_trial', 'Free Trial'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='stripe')
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    paypal_subscription_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.email} - {self.package.name}'

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True

    @property
    def is_trial(self):
        return self.payment_method == 'free_trial' and self.is_valid


class PackageFeature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='features')
    feature_text = models.CharField(max_length=255)
    is_included = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text='Display order (lower numbers appear first)')
    
    class Meta:
        ordering = ['order', 'feature_text']
    
    def __str__(self):
        return f'{self.package.name} - {self.feature_text}'


class PricingSection(models.Model):
    """CMS for the pricing section display"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default='Choose Your Plan')
    subtitle = models.TextField(blank=True, null=True, help_text='Optional subtitle or description')
    
    # Section styling
    background_color = models.CharField(max_length=50, default='#1a1a1a', help_text='Hex color code')
    text_color = models.CharField(max_length=50, default='#ffffff', help_text='Hex color code')
    
    # Badge for popular plan
    popular_badge_text = models.CharField(max_length=50, default='Most Popular')
    popular_badge_color = models.CharField(max_length=50, default='#d4ff00', help_text='Hex color code')
    
    # CTA button text
    free_plan_button_text = models.CharField(max_length=50, default='Get Started Free')
    paid_plan_button_text = models.CharField(max_length=50, default='Get Started')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pricing Section'
        verbose_name_plural = 'Pricing Section'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Ensure only one active pricing section
        if self.is_active:
            PricingSection.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)
