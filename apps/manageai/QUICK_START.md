# Quick Start Guide - AI Chat API

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Python 3.8+ installed
- Virtual environment activated
- Django project running
- OpenAI API key

---

## Step 1: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

**Or create a `.env` file in the project root:**
```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Step 2: Verify Installation

Check that migrations are applied:
```bash
python manage.py showmigrations manageai
```

You should see:
```
manageai
 [X] 0001_initial
```

---

## Step 3: Start the Server

```bash
python manage.py runserver
```

---

## Step 4: Get Authentication Token

First, sign in to get your JWT token:

```bash
curl -X POST http://localhost:8000/api/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access": "your_jwt_access_token",
  "refresh": "your_jwt_refresh_token"
}
```

**Save your access token!** You'll need it for all API calls.

---

## Step 5: Create a Chat Session

```bash
curl -X POST http://localhost:8000/api/ai/sessions/create/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "id": "3875f91d-8595-4369-9b85-cefe59839b4e",
  "user": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "messages": [],
  "message_count": 0
}
```

**Save your session ID!**

---

## Step 6: Start Chatting!

```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "user_input": "Hi, I want a workout plan for weight loss"
  }'
```

---

## Example Conversation Flow

### Message 1: Start conversation
```json
{
  "session_id": "3875f91d-8595-4369-9b85-cefe59839b4e",
  "user_input": "I want a workout plan for weight loss"
}
```

**Response:**
```json
{
  "session_id": "3875f91d-8595-4369-9b85-cefe59839b4e",
  "message": "To create the best workout plan for weight loss, I need some information about you. Could you please tell me your gender?",
  "workout": [],
  "diet": [],
  "summary": ""
}
```

### Message 2: Provide gender
```json
{
  "session_id": "3875f91d-8595-4369-9b85-cefe59839b4e",
  "user_input": "male"
}
```

### Continue providing information...
The AI will ask for:
1. Age
2. Weight (kg)
3. Height (feet)
4. Experience level (beginner/intermediate/advanced)
5. Health conditions
6. Goal timeline
7. Workout place (Home/Gym)

### Final Response: Complete Plan
After collecting all information, you'll receive:
```json
{
  "session_id": "3875f91d-8595-4369-9b85-cefe59839b4e",
  "message": "Here's your personalized plan!",
  "workout": [
    {
      "exercise": "Jumping Jacks",
      "sets": 3,
      "reps": "20-30"
    },
    {
      "exercise": "Push-ups",
      "sets": 3,
      "reps": "8-10"
    }
    // ... more exercises
  ],
  "diet": [
    {
      "meal": "Breakfast",
      "title": "High-Protein Oatmeal",
      "items": ["Oats", "Almond Milk", "Protein Powder", "Berries"],
      "nutrients": {
        "calories": 350,
        "protein": 25,
        "carbs": 45,
        "fats": 8
      }
    }
    // ... 3 more meals (Lunch, Snack, Dinner)
  ],
  "summary": "Male, 23 years old, 80 kg, 5.5 feet, beginner level, goal to lose weight in 3 months, prefers home workouts, no health conditions."
}
```

---

## Quick Reference: All Endpoints

| Action | Method | Endpoint | Body Required |
|--------|--------|----------|---------------|
| Create Session | POST | `/api/ai/sessions/create/` | No |
| Send Message | POST | `/api/ai/chat/` | Yes |
| List Sessions | GET | `/api/ai/sessions/` | No |
| Get Session | GET | `/api/ai/sessions/<id>/` | No |
| Delete Session | DELETE | `/api/ai/sessions/<id>/` | No |

---

## Using Postman

1. **Import these settings:**
   - Base URL: `http://localhost:8000/api/ai`
   - Authorization Type: Bearer Token
   - Token: `{{access_token}}`

2. **Create environment variables:**
   - `access_token`: Your JWT token
   - `session_id`: Your current session ID

3. **Test endpoints in this order:**
   1. POST `/sessions/create/`
   2. POST `/chat/` (multiple times)
   3. GET `/sessions/`
   4. GET `/sessions/{{session_id}}/`

---

## Using Python

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000/api"
EMAIL = "your_email@example.com"
PASSWORD = "your_password"

# 1. Login
response = requests.post(f"{BASE_URL}/signin/", json={
    "email": EMAIL,
    "password": PASSWORD
})
access_token = response.json()["access"]

# 2. Set headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 3. Create session
response = requests.post(
    f"{BASE_URL}/ai/sessions/create/",
    headers=headers
)
session_id = response.json()["id"]

# 4. Send message
response = requests.post(
    f"{BASE_URL}/ai/chat/",
    headers=headers,
    json={
        "session_id": session_id,
        "user_input": "I want a workout plan"
    }
)
print(response.json())
```

---

## Troubleshooting

### Error: "Authentication credentials were not provided"
**Fix:** Add the Authorization header with your JWT token

### Error: "OPENAI_API_KEY environment variable is not set"
**Fix:** Set the environment variable or add it to `.env` file

### Error: "Session not found"
**Fix:** Create a new session or use a valid session ID

### Error: "Invalid session_id format"
**Fix:** Ensure session_id is a valid UUID string

---

## Next Steps

1. ✅ Test basic conversation flow
2. ✅ Test getting workout plan
3. ✅ Test getting diet plan
4. ✅ View your sessions in admin panel: `http://localhost:8000/admin/`
5. ✅ Read full documentation: `API_DOCUMENTATION.md`

---

## Need Help?

- **Full API Documentation**: See `API_DOCUMENTATION.md`
- **Migration Guide**: See `README.md`
- **Technical Details**: See `MIGRATION_SUMMARY.md`

---

**Happy Coding! 💪🏋️‍♂️**
