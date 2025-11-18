# AI Chat API Documentation

This document describes the AI Chat API endpoints for the Django REST API implementation.

## Base URL
All endpoints are prefixed with `/api/ai/`

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Create New Chat Session
**Endpoint:** `POST /api/ai/sessions/create/`

**Description:** Creates a new chat session for the authenticated user.

**Request Body:** None

**Response:**
```json
{
  "id": "uuid-string",
  "user": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "messages": [],
  "message_count": 0
}
```

**Status Codes:**
- `201 Created` - Session created successfully
- `401 Unauthorized` - User not authenticated

---

### 2. Send Chat Message
**Endpoint:** `POST /api/ai/chat/`

**Description:** Send a message to the AI and receive a response. If `session_id` is not provided, a new session will be created automatically.

**Request Body:**
```json
{
  "user_input": "What's the best workout for weight loss?",
  "session_id": "uuid-string"  // Optional: omit to create new session
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "message": "To create the best workout plan for weight loss, I need some information about you. Could you please tell me your gender?",
  "workout": [],
  "diet": [],
  "summary": ""
}
```

**Example Response with Workout & Diet Plan:**
```json
{
  "session_id": "uuid-string",
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
    },
    {
      "meal": "Lunch",
      "title": "Grilled Chicken Salad",
      "items": ["Grilled Chicken", "Mixed Greens", "Cherry Tomatoes", "Olive Oil"],
      "nutrients": {
        "calories": 400,
        "protein": 35,
        "carbs": 20,
        "fats": 18
      }
    },
    {
      "meal": "Snack",
      "title": "Greek Yogurt with Nuts",
      "items": ["Greek Yogurt", "Almonds", "Honey"],
      "nutrients": {
        "calories": 200,
        "protein": 15,
        "carbs": 18,
        "fats": 10
      }
    },
    {
      "meal": "Dinner",
      "title": "Baked Salmon with Vegetables",
      "items": ["Salmon", "Broccoli", "Quinoa", "Lemon"],
      "nutrients": {
        "calories": 500,
        "protein": 40,
        "carbs": 30,
        "fats": 20
      }
    }
  ],
  "summary": "Male, 23 years old, 80 kg, 5.5 feet, beginner level, goal to lose weight in 3 months, prefers home workouts, no health conditions."
}
```

**Status Codes:**
- `200 OK` - Message processed successfully
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - User not authenticated
- `404 Not Found` - Session not found
- `500 Internal Server Error` - AI processing error

---

### 3. List All Chat Sessions
**Endpoint:** `GET /api/ai/sessions/`

**Description:** Retrieves all chat sessions for the authenticated user.

**Request Body:** None

**Response:**
```json
[
  {
    "id": "uuid-string-1",
    "user": 1,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:30:00Z",
    "messages": [
      {
        "id": "msg-uuid-1",
        "user_message": "Hi",
        "ai_message": "Hello! How can I assist you with your fitness goals today?",
        "workout": null,
        "diet": null,
        "summary": null,
        "created_at": "2024-01-01T12:00:00Z"
      }
    ],
    "message_count": 1
  },
  {
    "id": "uuid-string-2",
    "user": 1,
    "created_at": "2024-01-02T10:00:00Z",
    "updated_at": "2024-01-02T10:45:00Z",
    "messages": [...],
    "message_count": 5
  }
]
```

**Status Codes:**
- `200 OK` - Sessions retrieved successfully
- `401 Unauthorized` - User not authenticated

---

### 4. Get Chat Session Details
**Endpoint:** `GET /api/ai/sessions/<session_id>/`

**Description:** Retrieves a specific chat session with all its messages.

**Request Body:** None

**Response:**
```json
{
  "id": "uuid-string",
  "user": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z",
  "messages": [
    {
      "id": "msg-uuid-1",
      "user_message": "What is plank?",
      "ai_message": "The plank is a core strength exercise...",
      "workout": null,
      "diet": null,
      "summary": null,
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "user_message": "Can I do it for 10-15 seconds as a beginner?",
      "ai_message": "As a beginner, it's perfectly fine to start with 10-15 seconds...",
      "workout": [
        {
          "exercise": "Plank",
          "sets": 3,
          "duration": "10-15 seconds"
        }
      ],
      "diet": null,
      "summary": null,
      "created_at": "2024-01-01T12:05:00Z"
    }
  ],
  "message_count": 2
}
```

**Status Codes:**
- `200 OK` - Session retrieved successfully
- `401 Unauthorized` - User not authenticated
- `404 Not Found` - Session not found

---

### 5. Delete Chat Session
**Endpoint:** `DELETE /api/ai/sessions/<session_id>/`

**Description:** Deletes a specific chat session and all its messages.

**Request Body:** None

**Response:**
```json
{
  "message": "Chat session deleted successfully"
}
```

**Status Codes:**
- `204 No Content` - Session deleted successfully
- `401 Unauthorized` - User not authenticated
- `404 Not Found` - Session not found

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "details": "Detailed error information"
}
```

Or for validation errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Error message for another field"]
}
```

---

## AI Conversation Flow

The AI follows a conversational flow to collect user information before providing personalized plans:

### Required Information:
1. Gender (male/female)
2. Age (in years)
3. Weight (in kg)
4. Height (in feet)
5. Experience level (beginner, intermediate, advanced)
6. Health conditions or physical limitations
7. Fitness goal (gain muscle, lose weight, stay fit, etc.)
8. Preferred timeline to achieve the goal
9. Workout place (Home, Gym)
10. Dietary issues/allergies (optional)

### Behavior:
- The AI asks for ONE piece of information at a time
- Once all required information is collected, it provides:
  - Complete workout plan
  - Complete diet plan (4 meals: Breakfast, Lunch, Snack, Dinner)
  - Summary of user information
- For basic fitness questions, the AI can answer without collecting full information

---

## Environment Setup

Make sure to set up your OpenAI API key in your environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Or in your `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Database Models

### ChatSession
- `id` (UUID) - Primary key
- `user` (ForeignKey) - Reference to User model
- `created_at` (DateTime) - Session creation timestamp
- `updated_at` (DateTime) - Last update timestamp

### ChatMessage
- `id` (UUID) - Primary key
- `session` (ForeignKey) - Reference to ChatSession
- `user_message` (Text) - User's input message
- `ai_message` (Text) - AI's response message
- `workout` (JSON) - Workout plan data (if provided)
- `diet` (JSON) - Diet plan data (if provided)
- `summary` (Text) - User information summary (if provided)
- `created_at` (DateTime) - Message creation timestamp

---

## Testing with cURL

### Create a new session:
```bash
curl -X POST http://localhost:8000/api/ai/sessions/create/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Send a chat message:
```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hi, I want a workout plan", "session_id": "YOUR_SESSION_UUID"}'
```

### List all sessions:
```bash
curl -X GET http://localhost:8000/api/ai/sessions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get session details:
```bash
curl -X GET http://localhost:8000/api/ai/sessions/YOUR_SESSION_UUID/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Delete a session:
```bash
curl -X DELETE http://localhost:8000/api/ai/sessions/YOUR_SESSION_UUID/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```
