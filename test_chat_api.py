"""
Test script to call the chat API and see the error
"""
import requests
import json

url = "http://127.0.0.1:8001/api/chat/"

# Test data
data = {
    "user_input": "Hello, I want to get fit"
}

headers = {
    "Content-Type": "application/json"
}

print("Testing Chat API...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print("=" * 60)

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
