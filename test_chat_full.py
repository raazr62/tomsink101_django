"""
Comprehensive test for the chat API endpoint
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

# Create or get test user
user, created = User.objects.get_or_create(
    email='test@test.com',
    defaults={
        'is_active': True,
        'is_email_verified': True
    }
)

if created:
    user.set_password('testpass123')
    user.save()
    print(f"Created new user: {user.email}")
else:
    print(f"Using existing user: {user.email}")

# Try to create an auth token (if your project uses token auth)
try:
    token, created = Token.objects.get_or_create(user=user)
    print(f"Token: {token.key}")
except Exception as e:
    print(f"Token creation error (might not use token auth): {e}")
    token = None

# Create API client
client = APIClient()

print("\n" + "="*60)
print("Test 1: Without authentication")
print("="*60)
response = client.post(
    '/api/chat/',
    data={'user_input': 'Hello, I want to get fit'},
    format='json'
)
print(f"Status: {response.status_code}")
print(f"Response: {response.data if hasattr(response, 'data') else response.content}")

print("\n" + "="*60)
print("Test 2: With force_authenticate")
print("="*60)
client.force_authenticate(user=user)
try:
    response = client.post(
        '/api/chat/',
        data={'user_input': 'Hello'},
        format='json'
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 500:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Response: {json.dumps(response.data, indent=2)}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
