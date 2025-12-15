from django.utils.text import slugify
import secrets
import string
from django.core.mail import EmailMessage
from django.conf import settings

# Get Client IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Referral Code
def generate_referral_code(name):
    # Create slug from name (max 10 chars to keep code short)
    name_slug = slugify(name)[:10]
    
    # Generate 6 random alphanumeric characters
    random_chars = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    
    return f"{name_slug}-{random_chars}"

# Send Referral URL Email
def send_referral_url_email(user):
    subject = "Welcome to STRENNO - Your Referral Link"
    body = f"""
Hello {user.name},

Thank you for joining our waitlist! We're excited to have you on board.

Your personal referral link: {user.referral_link}

Share this link with friends and family to invite them to join STRENNO. You'll earn rewards when they sign up!

If you have any questions, feel free to reach out.

Best regards,
STRENNO Team
    """
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    email.send()