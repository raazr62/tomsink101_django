# AI Plan API Documentation

## Overview
The AI Plan API provides an intelligent fitness coaching system that uses OpenAI to generate personalized workout and diet plans. Each user has a single persistent session that maintains conversation history for contextual responses.

**Base URL**: `http://your-domain/api/`

**Authentication**: JWT Bearer Token (required for all endpoints)

**Content-Type**: `application/json`

---

## Authentication

All endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

To obtain a token, use the authentication endpoints (typically `/api/login/` or `/api/token/`).

---

## Endpoints

### 1. Chat with AI Coach

**Endpoint**: `POST /api/chat/`

**Description**: Send a message to the AI fitness coach and receive personalized advice, workout plans, or diet recommendations.

#### Request Headers
```
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

#### Request Body

```json
{
  "user_input": "string (required)",
  "summary": "string (optional)",
  "workout": [
    {
      "date": "YYYY-MM-DD",
      "exercise": [
        {
          "name": "string",
          "sets": integer,
          "reps": "string",
          "weight": "string",
          "description": "string",
          "pro_tips": ["string"]
        }
      ]
    }
  ],
  "diet": [
    {
      "date": "YYYY-MM-DD",
      "foods": [
        {
          "meal": "string",
          "title": "string",
          "items": ["string"],
          "nutrients": {
            "calories": integer,
            "protein": integer,
            "carbs": integer,
            "fats": integer
          }
        }
      ]
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_input` | string | Yes | User's question or request to the AI coach |
| `summary` | string | No | User profile summary for context (e.g., "Male, 25 years old, 80kg, goal: muscle gain") |
| `workout` | array | No | Current workout plan (for modifications or context) |
| `diet` | array | No | Current diet plan (for modifications or context) |

#### Response

**Success Response** (200 OK):

```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "uuid",
    "response": {
      "message": "string",
      "workout": [
        {
          "date": "2026-01-15",
          "exercise": [
            {
              "name": "Leg Press (Machine)",
              "sets": 4,
              "reps": "10–12",
              "weight": "60–90 kg",
              "description": "Sit with your back flat on the pad...",
              "pro_tips": [
                "Keep your lower back glued to the pad",
                "Control the lowering for 2–3 seconds"
              ]
            }
          ]
        }
      ],
      "diet": [
        {
          "date": "2026-01-15",
          "foods": [
            {
              "meal": "Breakfast",
              "title": "High-protein start",
              "items": [
                "Whole eggs + egg whites omelet",
                "Oats cooked with milk",
                "Banana"
              ],
              "nutrients": {
                "calories": 620,
                "protein": 45,
                "carbs": 70,
                "fats": 18
              }
            }
          ]
        }
      ],
      "summary": "Male, 20 years old, 100 kg, height 4'5\", fat-loss goal..."
    }
  }
}
```

**Error Response** (400 Bad Request):

```json
{
  "status": 400,
  "success": false,
  "message": "Invalid request data",
  "errors": {
    "user_input": ["This field is required."]
  }
}
```

**Error Response** (500 Internal Server Error):

```json
{
  "status": 500,
  "success": false,
  "message": "An error occurred: <error_details>"
}
```

---

### 2. Get Session History

**Endpoint**: `GET /api/sessions/`

**Description**: Retrieve the authenticated user's AI Plan session with all conversation history.

#### Request Headers
```
Authorization: Bearer <your_access_token>
```

#### Response

**Success Response** (200 OK):

```json
{
  "status": 200,
  "success": true,
  "message": "Session retrieved successfully",
  "data": {
    "id": "uuid",
    "user_email": "user@example.com",
    "conversation_count": 5,
    "conversations": [
      {
        "id": "uuid",
        "user_message": "What is my current workout plan?",
        "ai_message": "Based on your profile...",
        "summary": "Male, 25 years old...",
        "workout": [],
        "diet": [],
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-01-15T10:30:00Z"
      }
    ],
    "created_at": "2026-01-10T08:00:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
  }
}
```

**Error Response** (404 Not Found):

```json
{
  "status": 404,
  "success": false,
  "message": "No session found for this user"
}
```

---

## Usage Examples

### Example 1: First Conversation (Basic Question)

**Request:**
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is a plank exercise?"
  }'
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "3df759a7-1a59-41d6-887d-eaf56de2340c",
    "response": {
      "message": "A plank is an isometric core exercise that involves holding a push-up position for a period of time...",
      "workout": [],
      "diet": [],
      "summary": ""
    }
  }
}
```

---

### Example 2: Collecting User Information

**Request:**
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I am 20 years old, weigh 100 kg, and my goal is fat loss"
  }'
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "3df759a7-1a59-41d6-887d-eaf56de2340c",
    "response": {
      "message": "Thanks for sharing! To create the perfect fat-loss plan for you, could you tell me your height?",
      "workout": [],
      "diet": [],
      "summary": "Goal: fat loss; Age: 20; Weight: 100 kg"
    }
  }
}
```

---

### Example 3: Requesting a Complete Workout Plan

**Request:**
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Create a beginner workout plan for me",
    "summary": "Male, 20 years old, 100 kg, height 4 feet 5 inches, fat-loss goal, beginner"
  }'
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "3df759a7-1a59-41d6-887d-eaf56de2340c",
    "response": {
      "message": "Perfect! Here's a beginner-friendly fat-loss workout plan tailored for you...",
      "workout": [
        {
          "date": "2026-01-15",
          "exercise": [
            {
              "name": "Leg Press (Machine)",
              "sets": 4,
              "reps": "10–12",
              "weight": "60–90 kg",
              "description": "Sit with your back flat on the pad, feet shoulder-width on the platform...",
              "pro_tips": [
                "Keep your lower back glued to the pad",
                "Control the lowering for 2–3 seconds"
              ]
            },
            {
              "name": "Seated Chest Press (Machine)",
              "sets": 3,
              "reps": "10–12",
              "weight": "20–35 kg",
              "description": "Set the seat so handles are mid-chest...",
              "pro_tips": [
                "Keep shoulders down and back",
                "Stop 1 rep before form breaks"
              ]
            }
          ]
        }
      ],
      "diet": [],
      "summary": "Male, 20 years old, 100 kg, height 4'5\", fat-loss goal, beginner/new to training"
    }
  }
}
```

---

### Example 4: Requesting Diet Plan

**Request:**
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Give me a diet plan for fat loss",
    "summary": "Male, 20 years old, 100 kg, height 4 feet 5 inches, fat-loss goal, no dietary restrictions"
  }'
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "3df759a7-1a59-41d6-887d-eaf56de2340c",
    "response": {
      "message": "Here's a structured day of eating designed for fat loss...",
      "workout": [],
      "diet": [
        {
          "date": "2026-01-15",
          "foods": [
            {
              "meal": "Breakfast",
              "title": "High-protein start",
              "items": [
                "Whole eggs + egg whites omelet",
                "Oats cooked with milk",
                "Banana",
                "Cinnamon"
              ],
              "nutrients": {
                "calories": 620,
                "protein": 45,
                "carbs": 70,
                "fats": 18
              }
            },
            {
              "meal": "Lunch",
              "title": "Lean protein + carbs + veg",
              "items": [
                "Grilled chicken breast",
                "Basmati rice",
                "Mixed salad",
                "Olive oil + lemon dressing"
              ],
              "nutrients": {
                "calories": 720,
                "protein": 55,
                "carbs": 75,
                "fats": 20
              }
            }
          ]
        }
      ],
      "summary": "Male, 20 years old, 100 kg, height 4'5\", fat-loss goal, no dietary restrictions"
    }
  }
}
```

---

### Example 5: Modifying Existing Workout

**Request:**
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Add more cardio exercises to my workout",
    "summary": "Male, 20 years old, 100 kg, height 4 feet 5 inches, fat-loss goal",
    "workout": [
      {
        "date": "2026-01-15",
        "exercise": [
          {
            "name": "Leg Press",
            "sets": 4,
            "reps": "10–12",
            "weight": "60 kg"
          }
        ]
      }
    ]
  }'
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "3df759a7-1a59-41d6-887d-eaf56de2340c",
    "response": {
      "message": "I've updated your workout plan to include more cardio exercises...",
      "workout": [
        {
          "date": "2026-01-15",
          "exercise": [
            {
              "name": "Leg Press",
              "sets": 4,
              "reps": "10–12",
              "weight": "60 kg"
            },
            {
              "name": "Treadmill Running",
              "sets": 1,
              "reps": "20 minutes",
              "weight": "",
              "description": "Moderate pace cardio session",
              "pro_tips": ["Maintain steady breathing", "Keep good posture"]
            },
            {
              "name": "Jump Rope",
              "sets": 3,
              "reps": "2 minutes",
              "weight": "",
              "description": "High-intensity interval cardio",
              "pro_tips": ["Land softly on your toes", "Keep elbows close to body"]
            }
          ]
        }
      ],
      "diet": [],
      "summary": "Male, 20 years old, 100 kg, height 4'5\", fat-loss goal"
    }
  }
}
```

---

### Example 6: Retrieve Conversation History

**Request:**
```bash
curl -X GET http://localhost:8007/api/sessions/ \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Session retrieved successfully",
  "data": {
    "id": "3df759a7-1a59-41d6-887d-eaf56de2340c",
    "user_email": "user@example.com",
    "conversation_count": 3,
    "conversations": [
      {
        "id": "conv-uuid-1",
        "user_message": "Add more cardio exercises to my workout",
        "ai_message": "I've updated your workout plan to include more cardio...",
        "summary": "Male, 20 years old, 100 kg, height 4'5\", fat-loss goal",
        "workout": [...],
        "diet": [],
        "created_at": "2026-01-15T12:00:00Z",
        "updated_at": "2026-01-15T12:00:00Z"
      },
      {
        "id": "conv-uuid-2",
        "user_message": "Create a beginner workout plan for me",
        "ai_message": "Perfect! Here's a beginner-friendly fat-loss workout...",
        "summary": "Male, 20 years old, 100 kg, height 4'5\", fat-loss goal, beginner",
        "workout": [...],
        "diet": [],
        "created_at": "2026-01-15T11:00:00Z",
        "updated_at": "2026-01-15T11:00:00Z"
      }
    ],
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-01-15T12:00:00Z"
  }
}
```

---

## Python Test Script

Save this as `test_ai_plan_api.py`:

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8007/api"
ACCESS_TOKEN = "your_jwt_access_token_here"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


def test_chat_basic_question():
    """Test basic fitness question."""
    print("\\n=== Test 1: Basic Question ===")
    
    data = {
        "user_input": "What is a plank exercise?"
    }
    
    response = requests.post(
        f"{BASE_URL}/chat/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json().get('data', {}).get('session_id')


def test_chat_collect_info(session_id=None):
    """Test collecting user information."""
    print("\\n=== Test 2: Collect User Information ===")
    
    data = {
        "user_input": "I am 25 years old, weigh 80 kg, height 175 cm, and my goal is muscle gain"
    }
    
    response = requests.post(
        f"{BASE_URL}/chat/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json().get('data', {}).get('response', {}).get('summary')


def test_chat_workout_plan(summary):
    """Test requesting a workout plan."""
    print("\\n=== Test 3: Request Workout Plan ===")
    
    data = {
        "user_input": "Create a workout plan for muscle gain",
        "summary": summary
    }
    
    response = requests.post(
        f"{BASE_URL}/chat/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Message: {result.get('data', {}).get('response', {}).get('message')}")
    print(f"Workout exercises count: {len(result.get('data', {}).get('response', {}).get('workout', []))}")
    
    return result.get('data', {}).get('response', {}).get('workout', [])


def test_chat_diet_plan(summary):
    """Test requesting a diet plan."""
    print("\\n=== Test 4: Request Diet Plan ===")
    
    data = {
        "user_input": "Give me a diet plan for muscle gain",
        "summary": summary
    }
    
    response = requests.post(
        f"{BASE_URL}/chat/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Message: {result.get('data', {}).get('response', {}).get('message')}")
    print(f"Diet meals count: {len(result.get('data', {}).get('response', {}).get('diet', []))}")


def test_modify_workout(summary, current_workout):
    """Test modifying existing workout."""
    print("\\n=== Test 5: Modify Workout ===")
    
    data = {
        "user_input": "Add more leg exercises",
        "summary": summary,
        "workout": current_workout
    }
    
    response = requests.post(
        f"{BASE_URL}/chat/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Message: {result.get('data', {}).get('response', {}).get('message')}")


def test_get_session():
    """Test retrieving session history."""
    print("\\n=== Test 6: Get Session History ===")
    
    response = requests.get(
        f"{BASE_URL}/sessions/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Session ID: {result.get('data', {}).get('id')}")
    print(f"Conversation Count: {result.get('data', {}).get('conversation_count')}")


if __name__ == "__main__":
    print("=== AI Plan API Test Suite ===")
    print(f"Testing against: {BASE_URL}")
    
    # Run tests sequentially
    session_id = test_chat_basic_question()
    summary = test_chat_collect_info(session_id)
    
    if summary:
        workout = test_chat_workout_plan(summary)
        test_chat_diet_plan(summary)
        
        if workout:
            test_modify_workout(summary, workout)
    
    test_get_session()
    
    print("\\n=== All Tests Complete ===")
```

---

## Important Notes

### Session Management
- **One Session Per User**: Each user has exactly one AI Plan session that persists across all conversations
- **Session ID**: The session ID is automatically created on first chat and returned in every response
- **Conversation History**: All previous conversations are automatically included as context for new messages

### Conversation Context
The AI considers:
1. **Previous conversations**: Last 10 messages for context
2. **User profile summary**: Continuously updated throughout the conversation
3. **Current workout plan**: If provided, used for modifications
4. **Current diet plan**: If provided, used for modifications

### Response Behavior
- **Basic questions**: Returns only `message`, with empty `workout` and `diet` arrays
- **Plan requests**: Returns `message` plus populated `workout` and/or `diet` arrays
- **Modifications**: Returns `message` plus the COMPLETE updated plan (not just changes)
- **Summary updates**: The `summary` field accumulates user information over time

### Error Handling
- **401 Unauthorized**: Missing or invalid JWT token
- **400 Bad Request**: Invalid request format or missing required fields
- **404 Not Found**: Session doesn't exist (only for GET /sessions/)
- **500 Internal Server Error**: OpenAI API error, JSON parsing error, or server issue

### Best Practices
1. Always provide the latest `summary` from previous responses for continuity
2. Include current `workout` and `diet` when requesting modifications
3. Handle the `summary` field carefully - it accumulates user profile data
4. The AI focuses only on fitness-related queries and will refuse non-fitness questions

---

## Comparison with FastAPI Version

### Key Differences

| Feature | FastAPI Version | Django Version |
|---------|-----------------|----------------|
| Storage | JSON file (`workout_history.json`) | PostgreSQL/SQLite database |
| Session per user | Multiple (via session_id parameter) | One (OneToOne with User) |
| Authentication | None (open API) | JWT Bearer Token (required) |
| User association | None | Tied to authenticated user |
| Session retrieval | Not available | Available via GET /sessions/ |
| Response format | Direct JSON | Wrapped in standard response format |

### Migration Considerations

If migrating from the FastAPI version:
1. Each user now has **one persistent session** instead of multiple session IDs
2. All endpoints require **authentication**
3. Session management is **automatic** - no need to pass session_id
4. Old conversation data in `workout_history.json` can be migrated via a management command if needed

---

## Troubleshooting

### "OPENAI_API_KEY environment variable is not set"
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Restart the Django server after adding the key

### "No session found for this user"
- This occurs when calling GET /sessions/ before any chat
- Send at least one POST /chat/ request to create the session

### "Invalid JSON response from AI"
- Check if the OpenAI API is responding correctly
- Verify the API key is valid and has sufficient credits
- Review the system prompt format

### 401 Unauthorized
- Ensure you're including the JWT token in the Authorization header
- Verify the token hasn't expired (default: 1 day)
- Use the token refresh endpoint if needed

---

## Support

For issues or questions:
1. Check the Django logs for detailed error messages
2. Verify your OpenAI API key is valid
3. Ensure all migrations are applied: `python manage.py migrate`
4. Test authentication separately before testing AI Plan endpoints
