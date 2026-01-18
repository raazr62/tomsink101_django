"""
OpenAI utility functions for the Django project.
"""

from openai import OpenAI
from django.conf import settings


def get_openai_client():
    """Initialize OpenAI client with API key from environment."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)
