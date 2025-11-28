import secrets
from django.core.mail import EmailMessage
from django.conf import settings

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))

def send_normal_mail(data):
    email = EmailMessage(
        subject=data['subject'],
        body=data['body'],
        from_email=settings.EMAIL_HOST_USER,
        to=data['to']
    )
    email.send()

def send_verification_otp_email(user, otp):
    """Send OTP email for email verification"""
    subject = "Verify Your Email Address - OTP"
    body = f"""
Hello {user.email},

Thank you for signing up! Please use the following OTP to verify your email address:

Your OTP: {otp}

This OTP will expire in 10 minutes.

If you didn't create this account, please ignore this email.

Best regards,
Strenno Team
    """
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    email.send()

def send_verification_success_email(user):
    """Send confirmation email after successful verification"""
    subject = "Email Verified Successfully"
    body = f"""
Hello {user.email},

Your email has been successfully verified! You can now access all features of your account.

Best regards,
Strenno Team
    """
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    email.send()