from cloudinary.utils import cloudinary_url
from django.utils.text import slugify
import secrets, string

def get_cloudinary_url(file_field):
    if not file_field:
        return None
    url, _ = cloudinary_url(str(file_field), secure=True)
    return url

def preview_image(file_field):
    if not file_field:
        return None
    url, _ = cloudinary_url(str(file_field), secure=True)
    return url

def generate_referral_code(name):
    # Create slug from name (max 10 chars to keep code short)
    name_slug = slugify(name)[:10]

    # Generate 6 random alphanumeric characters
    random_chars = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    
    return f"{name_slug}-{random_chars}"