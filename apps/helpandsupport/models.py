from django.db import models
from django.core.validators import EmailValidator, RegexValidator


class ContactSupport(models.Model):
    """
    Singleton model to store contact support information.
    Displays email, phone, and average response time.
    """
    support_email = models.EmailField(
        max_length=255,
        validators=[EmailValidator()],
        help_text="Support email address (e.g., support@example.com)"
    )
    
    support_phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        help_text="Support phone number (e.g., +1 (123) 456-7890)"
    )
    
    support_phone_display = models.CharField(
        max_length=30,
        blank=True,
        help_text="Formatted phone number for display (e.g., +1 (123) 456-7890)"
    )
    
    average_response_time = models.CharField(
        max_length=50,
        default="Under 2 hours",
        help_text="Average response time display text (e.g., 'Under 2 hours')"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Set to false to disable contact support section"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_support'
        verbose_name = 'Contact Support'
        verbose_name_plural = 'Contact Support'
    
    def __str__(self):
        return f"Contact Support - {self.support_email}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        if not self.pk and ContactSupport.objects.exists():
            raise ValueError('Only one ContactSupport instance is allowed.')
        
        # Auto-format phone display if not provided
        if not self.support_phone_display:
            self.support_phone_display = self.support_phone
        
        return super().save(*args, **kwargs)


class LegalDocument(models.Model):
    """
    Model to store legal documents like Terms of Service and Privacy Policy.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('terms_of_service', 'Terms of Service'),
        ('privacy_policy', 'Privacy Policy'),
        ('cookie_policy', 'Cookie Policy'),
        ('gdpr_compliance', 'GDPR Compliance'),
        ('disclaimer', 'Disclaimer'),
        ('refund_policy', 'Refund Policy'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Document title (e.g., 'Terms of Service')"
    )
    
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        unique=True,
        help_text="Type of legal document"
    )
    
    content = models.TextField(
        help_text="Full content of the legal document (supports HTML)"
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL-friendly version of title (auto-generated)"
    )
    
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Document version number"
    )
    
    effective_date = models.DateField(
        help_text="Date when this version becomes effective"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Set to false to hide this document"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'legal_documents'
        verbose_name = 'Legal Document'
        verbose_name_plural = 'Legal Documents'
        ordering = ['order', 'title']
    
    def __str__(self):
        return f"{self.title} (v{self.version})"


class SupportTicket(models.Model):
    """
    Model to track user support tickets/inquiries.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_for_user', 'Waiting for User'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated ticket number"
    )
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='support_tickets',
        null=True,
        blank=True,
        help_text="User who submitted the ticket (optional for anonymous)"
    )
    
    email = models.EmailField(
        help_text="Contact email for ticket updates"
    )
    
    subject = models.CharField(
        max_length=255,
        help_text="Ticket subject/title"
    )
    
    message = models.TextField(
        help_text="Detailed description of the issue"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text="Current status of the ticket"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the ticket"
    )
    
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes (not visible to user)"
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when ticket was resolved"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'support_tickets'
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        # Auto-generate ticket number if not exists
        if not self.ticket_number:
            import random
            import string
            self.ticket_number = 'TKT-' + ''.join(random.choices(string.digits, k=8))
        
        return super().save(*args, **kwargs)
