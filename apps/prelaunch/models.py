from django.db import models
from django.conf import settings
from .helpers import generate_referral_code

# Prelaunch User
class PrelaunchUser(models.Model):

    name = models.CharField(max_length=255, help_text="User's full name")
    email = models.EmailField(unique=True, db_index=True, help_text="User's email address (must be unique)")
    referral_code = models.CharField(max_length=50, unique=True, db_index=True,help_text="User's unique referral code to share with others")
    referred_by = models.CharField(max_length=50, blank=True, null=True, db_index=True, help_text="Referral code of the person who invited this user")
    ip_address = models.GenericIPAddressField(blank=True, null=True,help_text="IP address for fraud detection")
    user_agent = models.TextField(blank=True, null=True, help_text="Browser user agent for fraud detection")
    activated = models.BooleanField(default=False, help_text="Whether this user has activated their main account")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pre-Launch User'
        verbose_name_plural = 'Pre-Launch Users'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['email']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['referred_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            # Generate a unique referral code
            while True:
                code = generate_referral_code(self.name)
                if not PrelaunchUser.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    @property
    def referral_link(self):
        base_url = getattr(settings, 'SITE_URL', 'https://astonishing-cupcake-ab36d3.netlify.app')
        return f"{base_url}/sign-up/?ref={self.referral_code}"

    @property
    def referral_count(self):
        return self.referrals_made.count()

    def get_referrals(self):
        return PrelaunchUser.objects.filter(referred_by=self.referral_code)

# Referral Model
class PrelaunchReferral(models.Model):
    parent_referral_code = models.CharField(max_length=50, db_index=True, help_text="Referral code of the inviter")
    child_email = models.EmailField(db_index=True, help_text="Email of the user who was referred")
    child_user = models.ForeignKey(PrelaunchUser, on_delete=models.CASCADE, related_name='referral_records', null=True, blank=True,help_text="The user who was referred (null for main app users)")
    parent_user = models.ForeignKey(PrelaunchUser, on_delete=models.CASCADE, related_name='referrals_made', null=True, blank=True, help_text="The user who made the referral")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        indexes = [
            models.Index(fields=['parent_referral_code']),
            models.Index(fields=['child_email']),
            models.Index(fields=['-created_at']),
        ]
        # Prevent duplicate referral entries
        unique_together = [['parent_referral_code', 'child_email']]

    def __str__(self):
        return f"{self.parent_referral_code} → {self.child_email}"

    def save(self, *args, **kwargs):
        if not self.parent_user:
            try:
                self.parent_user = PrelaunchUser.objects.get(referral_code=self.parent_referral_code)
            except PrelaunchUser.DoesNotExist:
                pass
        super().save(*args, **kwargs)
