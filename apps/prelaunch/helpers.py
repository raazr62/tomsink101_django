from django.utils.text import slugify
import secrets
import string

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
