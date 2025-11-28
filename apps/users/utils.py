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
    
    
    
from google.auth.transport import requests
from google.oauth2 import id_token
from apps.users.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class Google():
    @staticmethod
    def validate(access_token):  
        try:
            id_info = id_token.verify_oauth2_token(
                access_token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer')
            return id_info
        except ValueError as e:
            print(f"Token verification failed: {e}")
            raise AuthenticationFailed("Token is invalid")


def register_with_google(provider, email, first_name, last_name):
    old_user = User.objects.filter(email=email)
    if old_user.exists():
        if provider == old_user[0].auth_provider:
            register_user = authenticate(email=email, password=settings.GOOGLE_SECRET_KEY)
            tokens = register_user.tokens()
            return {
                'full_name': register_user.get_full_name(),
                'email': register_user.email,
                'refresh_token': str(tokens.get('refresh')),
                'access_token': str(tokens.get('access')),
            }
        
        else:
            raise AuthenticationFailed('Email is already registered with {} '.format(old_user[0].auth_provider))

    else:
        new_user = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': settings.GOOGLE_SECRET_KEY
        }
        user = User.objects.create_user(**new_user)
        user.auth_provider = provider
        user.is_verified = True
        user.save()
        login_user = authenticate(email=email, password=settings.GOOGLE_SECRET_KEY)
        tokens = login_user.tokens()
        return {
            'full_name': login_user.get_full_name(),
            'email': login_user.email,
            'refresh_token': str(tokens.get('refresh')),
            'access_token': str(tokens.get('access')),
        }