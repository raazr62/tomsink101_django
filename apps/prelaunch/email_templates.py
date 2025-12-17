from django.core.mail import EmailMessage
from django.conf import settings

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