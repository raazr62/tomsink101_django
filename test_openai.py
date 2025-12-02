"""
Test script to verify OpenAI API key from .env file
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

print("=" * 60)
print("OpenAI API Key Test")
print("=" * 60)

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
    print("Please check your .env file")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...{api_key[-4:]}")
print("\nTesting API connection...")

try:
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Make a simple test API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, API test successful!' in one sentence."}
        ],
        max_tokens=50,
        temperature=0.5
    )
    
    # Extract response
    ai_reply = response.choices[0].message.content.strip()
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS: API connection working!")
    print("=" * 60)
    print(f"AI Response: {ai_reply}")
    print(f"\nModel used: {response.model}")
    print(f"Tokens used: {response.usage.total_tokens}")
    print("=" * 60)
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ ERROR: API test failed")
    print("=" * 60)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("=" * 60)
    exit(1)
