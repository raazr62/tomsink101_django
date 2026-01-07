from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
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

# Verification template Email
def send_verification_success_email(user):
    name = user.name
    referral_link = ""
    profile = getattr(user, 'profile', None)

    if profile:
        name = profile.name or user.email
        referral_link = profile.referral_link or ""

    subject = f"You're in, {name} — here are your rewards"
    context = {
        'user_name': name,
        'referral_link': referral_link,
        'habit_guide_url': f"{settings.SITE_URL}/media/downloads/Habit%20and%20Accountability%20Guide.pdf",
        'nutrition_guide_url': f"{settings.SITE_URL}/media/downloads/Strenno%20Nutrition%20and%20Diet%20Guide.pdf",
        'tracker_url': f"{settings.SITE_URL}/media/downloads/Strenno%20Daily%20Fitness%20Tracker.pdf",
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