# AI Plan API - Quick Reference

## Endpoints

### 1. Chat with AI Coach
```
POST /api/chat/
Authorization: Bearer <token>
```

**Minimal Request:**
```json
{
  "user_input": "Your question here"
}
```

**Full Request:**
```json
{
  "user_input": "Your question here",
  "summary": "User profile summary",
  "workout": [...],
  "diet": [...]
}
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "uuid",
    "response": {
      "message": "AI response",
      "workout": [...],
      "diet": [...],
      "summary": "Updated profile"
    }
  }
}
```

---

### 2. Get Session History
```
GET /api/sessions/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Session retrieved successfully",
  "data": {
    "id": "uuid",
    "user_email": "user@example.com",
    "conversation_count": 5,
    "conversations": [...],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

---

## Quick Testing with cURL

### Get JWT Token (Login First)
```bash
curl -X POST http://localhost:8007/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"
  }'
```

### Chat - Basic Question
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is a plank?"
  }'
```

### Chat - Request Workout Plan
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Create a workout plan for fat loss",
    "summary": "Male, 25 years old, 80kg, beginner"
  }'
```

### Get Session History
```bash
curl -X GET http://localhost:8007/api/sessions/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Python Quick Test

```python
import requests

BASE_URL = "http://localhost:8007/api"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Send a message
response = requests.post(
    f"{BASE_URL}/chat/",
    headers=headers,
    json={"user_input": "What is a plank?"}
)

print(response.json())

# Get history
response = requests.get(
    f"{BASE_URL}/sessions/",
    headers=headers
)

print(response.json())
```

---

## Key Features

✓ **One Session Per User** - Automatically managed  
✓ **Conversation History** - Last 10 messages used as context  
✓ **Profile Summary** - Accumulated across conversations  
✓ **Workout Plans** - Complete exercise programs with sets/reps  
✓ **Diet Plans** - Meal plans with nutritional information  
✓ **Plan Modifications** - Update existing plans  
✓ **JWT Authentication** - Secure user access  

---

## Response Patterns

| User Input Type | Response Contains |
|----------------|-------------------|
| Basic question | `message` only |
| Request workout | `message` + `workout` array |
| Request diet | `message` + `diet` array |
| Modify plan | `message` + updated full plan |
| Profile info | `message` + updated `summary` |

---

## Status Codes

- **200** - Success
- **400** - Bad request (invalid data)
- **401** - Unauthorized (missing/invalid token)
- **404** - Session not found
- **500** - Server error (OpenAI API issue, etc.)

---

## Notes

- Session is created automatically on first chat
- Session ID is returned in every response
- No need to pass session_id (tied to authenticated user)
- Always include latest `summary` for continuity
- AI only responds to fitness-related questions
