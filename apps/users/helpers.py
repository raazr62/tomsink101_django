from cloudinary.utils import cloudinary_url

def get_cloudinary_url(file_field):
    if not file_field:
        return None
    url, _ = cloudinary_url(str(file_field), secure=True)
    return url