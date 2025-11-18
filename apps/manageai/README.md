# AI Chat - Django REST API Implementation

## Overview

This Django REST API implementation replaces the FastAPI version (`ai_chat/ai_chat.py`) with a fully integrated Django solution in the `apps/manageai` app. The implementation provides AI-powered fitness coaching with conversation history stored in a PostgreSQL/SQLite database.

## What Was Migrated

### From FastAPI (`ai_chat/ai_chat.py`)
- ✅ Chat endpoint with OpenAI integration
- ✅ Session management (file-based → database-based)
- ✅ Conversation history tracking
- ✅ Workout and diet plan generation
- ✅ AI system prompt for fitness coaching
- ✅ JSON response parsing and validation

### New Features Added
- ✅ User authentication (JWT-based)
- ✅ Database persistence for sessions and messages
- ✅ RESTful API endpoints
- ✅ Admin panel integration
- ✅ Session listing and detail views
- ✅ Session deletion capability

## File Structure

```
apps/manageai/
├── __init__.py
├── admin.py                    # Admin panel configuration
├── apps.py                     # App configuration
├── models.py                   # ChatSession & ChatMessage models
├── serializers.py              # DRF serializers
├── views.py                    # API views
├── urls.py                     # URL routing
├── API_DOCUMENTATION.md        # Detailed API documentation
├── migrations/
│   └── 0001_initial.py         # Initial database migration
└── tests.py
```

## Key Differences from FastAPI Version

| Feature | FastAPI Version | Django REST Version |
|---------|----------------|---------------------|
| Storage | JSON files | Database (Django ORM) |
| Auth | None | JWT authentication required |
| User Sessions | Session ID only | Linked to authenticated users |
| Admin Panel | None | Full admin interface |
| Session Management | Create/Continue | Create/List/Detail/Delete |
| API Style | FastAPI | Django REST Framework |

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the project root or set environment variable:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Install Dependencies

The required packages have been added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key packages:
- `openai==2.8.0` - OpenAI API client
- `python-dotenv==1.2.1` - Environment variable management

### 3. Run Migrations

Migrations have already been created and applied:

```bash
python manage.py makemigrations manageai
python manage.py migrate manageai
```

### 4. Access the API

The API is available at: `http://localhost:8000/api/ai/`

## API Endpoints

### Base URL: `/api/ai/`

1. **POST** `/chat/` - Send chat message
2. **GET** `/sessions/` - List all sessions
3. **POST** `/sessions/create/` - Create new session
4. **GET** `/sessions/<uuid>/` - Get session details
5. **DELETE** `/sessions/<uuid>/` - Delete session

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for detailed endpoint documentation.

## Database Models

### ChatSession
```python
- id (UUID) - Primary key
- user (ForeignKey) - Reference to User
- created_at (DateTime)
- updated_at (DateTime)
```

### ChatMessage
```python
- id (UUID) - Primary key
- session (ForeignKey) - Reference to ChatSession
- user_message (Text)
- ai_message (Text)
- workout (JSON) - Nullable
- diet (JSON) - Nullable
- summary (Text) - Nullable
- created_at (DateTime)
```

## Admin Panel

The models are registered in the Django admin with:
- Inline message viewing in session detail
- Filtering by date and user
- Search functionality
- Read-only fields for system-generated data

Access admin at: `http://localhost:8000/admin/`

## Authentication

All API endpoints require JWT authentication:

```bash
# Get token
POST /api/signin/
{
  "email": "user@example.com",
  "password": "password"
}

# Use token
Authorization: Bearer <your_jwt_token>
```

## Example Usage

### 1. Create a new session
```bash
curl -X POST http://localhost:8000/api/ai/sessions/create/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Send a message
```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I want a workout plan for weight loss",
    "session_id": "YOUR_SESSION_UUID"
  }'
```

### 3. List all sessions
```bash
curl -X GET http://localhost:8000/api/ai/sessions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Migration from FastAPI

If you were using the FastAPI version, your existing chat data is stored in `ai_chat/chat_sessions.json`. This data is not automatically migrated. You can:

1. **Option 1**: Keep the old data as a backup
2. **Option 2**: Write a custom migration script to import JSON data into the database

The new Django implementation stores data in the database with user associations, providing better data integrity and querying capabilities.

## AI System Prompt

The AI system prompt is identical to the FastAPI version and follows the same conversation flow:

1. Collects user information (gender, age, weight, height, etc.)
2. Asks one question at a time
3. Once complete, provides:
   - Personalized workout plan
   - Complete diet plan (4 meals)
   - User information summary

## Testing

You can test the endpoints using:
- cURL (see examples above)
- Postman
- Django REST Framework browsable API (when authenticated)
- Python requests library

## Troubleshooting

### Issue: "OPENAI_API_KEY environment variable is not set"
**Solution**: Set the environment variable or add it to your `.env` file

### Issue: "Authentication credentials were not provided"
**Solution**: Include the JWT token in the Authorization header

### Issue: "Module 'openai' not found"
**Solution**: Run `pip install openai python-dotenv`

## Future Enhancements

Potential improvements:
- [ ] Add pagination for session lists
- [ ] Add filtering and search for sessions
- [ ] Implement websocket support for real-time chat
- [ ] Add export functionality for chat history
- [ ] Implement rate limiting
- [ ] Add chat session naming/tagging
- [ ] Add analytics and reporting

## Support

For detailed API documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

For issues or questions, check the Django and DRF documentation:
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [OpenAI API](https://platform.openai.com/docs/)
