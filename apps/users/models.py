from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from .managers import UserManager
from django.contrib.auth.hashers import check_password
from cloudinary.models import CloudinaryField
from django.conf import settings
from .helpers import generate_referral_code

# AbstractBase User
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_otp = models.CharField(max_length=255, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.IntegerField(default=0)
    auth_provider = models.CharField(max_length=50, default='email')  # 'email', 'google', etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email or f"User {self.pk}"
    
    # Check OTP expiration
    def is_verification_otp_expired(self):
        if not self.otp_expires_at:
            return True
        return timezone.now() > self.otp_expires_at
    
    # Check OTP match
    def check_verification_otp(self, raw_otp):
        if not self.email_verification_otp:
            return False
        return check_password(raw_otp, self.email_verification_otp)

# Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=30, blank=True)
    accepted_terms = models.BooleanField(default=False)
    avatar = CloudinaryField('image', blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    referral_code = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True, help_text="User's unique referral code to share with others")
    referred_by = models.CharField(max_length=50, blank=True, null=True, db_index=True, help_text="Referral code of the person who invited this user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.name:
            return self.name
        if self.user and self.user.email:
            return self.user.email
        return "Profile"

    # Generate referral
    def save(self, *args, **kwargs):
        if not self.referral_code and self.name:
            # Generate a unique referral code
            while True:
                code = generate_referral_code(self.name)
                if not Profile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    # Referral link
    @property
    def referral_link(self):
        base_url = getattr(settings, 'SITE_URL', 'https://astonishing-cupcake-ab36d3.netlify.app')
        return f"{base_url}/sign-up/?ref={self.referral_code}"

    # Referral count
    @property
    def referral_count(self):
        return self.referrals_made.count()

    def get_referrals(self):
        return Profile.objects.filter(referred_by=self.referral_code)

# Referral
class UserReferral(models.Model):
    parent_referral_code = models.CharField(max_length=50, db_index=True,help_text="Referral code of the inviter")
    child_email = models.EmailField(db_index=True, help_text="Email of the user who was referred")
    child_profile = models.ForeignKey(Profile, on_delete=models.CASCADE,
    related_name='referral_records', help_text="The profile who was referred")
    parent_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='referrals_made', null=True, blank=True, help_text="The profile who made the referral")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Referral'
        verbose_name_plural = 'User Referrals'
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
        if not self.parent_profile:
            try:
                self.parent_profile = Profile.objects.get(referral_code=self.parent_referral_code)
            except Profile.DoesNotExist:
                pass
        super().save(*args, **kwargs)

# OTP Purpose Choices
PURPOSE = (
    ('password_reset', 'Password Reset'),
    ('login', 'Login'),
    ('delete_account', 'Delete Account')
)

# OTP 
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=255)
    is_verify = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    purpose = models.CharField(max_length=50, blank=True, null=True, choices=PURPOSE) # login, password reset, 2fa etc
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=3)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def check_otp(self, raw_otp):
        return check_password(raw_otp, self.otp)

