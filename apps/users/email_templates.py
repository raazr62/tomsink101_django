import secrets
from django.core.mail import EmailMessage
from django.conf import settings
from google.auth.transport import requests
from google.oauth2 import id_token
from apps.users.models import User, Profile
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# Generate OTP
def generate_otp(length=6):
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))

# Normal Email
def send_normal_mail(data):
    email = EmailMessage(
        subject=data['subject'],
        body=data['body'],
        from_email=settings.EMAIL_HOST_USER,
        to=data['to']
    )
    email.send()

# Verification Email
def send_verification_otp_email(user, otp):
    referral_link = ""
    try:
        if hasattr(user, 'profile'):
            referral_link = user.profile.referral_link
    except:
        pass
    
    subject = "Verify Your Email Address - OTP"
    body = f"""
Hello {user.email},

Thank you for signing up! Please use the following OTP to verify your email address:

Your OTP: {otp}

This OTP will expire in 10 minutes.

{ "Your referral link: " + referral_link if referral_link else "" }

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

# Verification Success Email
def send_verification_success_email(user):
    name = user.email
    referral_link = ""
    profile = getattr(user, 'profile', None)

    if profile:
        name = profile.name or user.email
        referral_link = profile.referral_link or ""

    subject = f"You're in, {name} — here are your rewards"
    context = {
        'user_name': name,
        'referral_link': referral_link,
    }

    html_message = render_to_string('email/verification_success.html', context)

    text_body_lines = [
        f"Hey {name}, you're officially in!",
        "",
        "Thanks for signing up early — that’s dedication. You now have first access to STRENNO, ",
        "an AI-powered fitness app designed for anyone who's tired of long hours wrecking their motivation.",
        "",
        "As promised, your rewards are ready to use straight away.",
    ]

    if referral_link:
        text_body_lines.append(f"Claim your free trial: {referral_link}")
        text_body_lines.append("")

    text_body_lines.extend([
        "We'll email you the moment early access opens. Until then, enjoy the other rewards, ",
        "set a few small goals and get ready for a version of fitness that finally fits your routine!",
        "",
        "Small steps add up faster than you think — you've just taken the first one.",
        "",
        "— The STRENNO team",
    ])

    text_message = "\n".join(text_body_lines)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)

# Google Authentication
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

# Register or Authenticate with Google
def register_with_google(provider, email, first_name, last_name):
    old_user = User.objects.filter(email=email)
    if old_user.exists():
        user = old_user[0]
        # If user exists, authenticate them
        if hasattr(user, 'auth_provider') and provider == user.auth_provider:
            refresh = RefreshToken.for_user(user)
            return {
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'email': user.email,
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
            }
        elif not hasattr(user, 'auth_provider'):
            # Update existing user to have Google auth
            user.auth_provider = provider
            user.is_email_verified = True
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            return {
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'email': user.email,
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
            }
        else:
            raise AuthenticationFailed(f'Email is already registered with {getattr(user, "auth_provider", "another provider")}')
    else:
        # Create new user
        user = User.objects.create_user(
            email=email,
            password=settings.GOOGLE_SECRET_KEY,
            first_name=first_name,
            last_name=last_name
        )
        user.auth_provider = provider
        user.is_email_verified = True
        user.is_active = True
        user.save()
        
        # Create profile
        Profile.objects.create(
            user=user,
            name=f"{first_name} {last_name}".strip() or email
        )
        
        refresh = RefreshToken.for_user(user)
        return {
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'email': user.email,
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
        }