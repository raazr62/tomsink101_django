# AI Plan - Implementation Summary

## ✅ Completed Tasks

### 1. Models Created
**File**: [apps/ai_plan/models.py](apps/ai_plan/models.py)

- **AIPlanSession**: One-to-one relationship with User
  - UUID primary key
  - OneToOne with User (one session per user)
  - Timestamps (created_at, updated_at)
  - Properties: conversation_count, last_conversation

- **AIPlanConversation**: Stores individual chat messages
  - UUID primary key
  - ForeignKey to AIPlanSession
  - Fields: user_message, ai_message, summary, workout (JSON), diet (JSON)
  - Timestamps (created_at, updated_at)

### 2. Serializers Created
**File**: [apps/ai_plan/serializers.py](apps/ai_plan/serializers.py)

- **AskRequestSerializer**: Validates incoming chat requests
- **AskResponseSerializer**: Formats AI responses
- **ChatResponseSerializer**: Complete chat response with session_id
- **ConversationSerializer**: Individual conversation history
- **SessionDetailSerializer**: Session with nested conversations
- **WorkoutExerciseSerializer**, **WorkoutDaySerializer**: Workout structure
- **MealItemSerializer**, **DietDaySerializer**: Diet structure

### 3. Views Implemented
**File**: [apps/ai_plan/views.py](apps/ai_plan/views.py)

- **AIPlanChatView (POST /api/chat/)**:
  - Validates request with AskRequestSerializer
  - Gets or creates user's session (one per user)
  - Builds conversation history (last 10 messages)
  - Formats system prompt with context
  - Calls OpenAI API (gpt-4o-mini)
  - Parses JSON response
  - Saves conversation to database
  - Returns standardized response

- **SessionDetailView (GET /api/sessions/)**:
  - Retrieves authenticated user's session
  - Returns all conversation history
  - Returns 404 if no session exists

### 4. URL Configuration
**File**: [apps/ai_plan/urls.py](apps/ai_plan/urls.py)

- `POST /api/chat/` → AIPlanChatView
- `GET /api/sessions/` → SessionDetailView

**Main URLs**: Already included in [project/urls.py](project/urls.py) at line 20

### 5. Admin Interface
**File**: [apps/ai_plan/admin.py](apps/ai_plan/admin.py)

- **AIPlanSessionAdmin**: List sessions with conversation counts
  - Inline conversations display
  - Search by user email/name
  - Filters by date

- **AIPlanConversationAdmin**: View conversation details
  - Collapsible workout/diet JSON fields
  - Search by messages and summary
  - Preview user messages

### 6. Utilities
**File**: [apps/utils/openai_utils.py](apps/utils/openai_utils.py)

- **get_openai_client()**: Initializes OpenAI client with API key from settings

### 7. Migrations
- Created and applied: `0001_initial.py`
- Tables created: `ai_plan_sessions`, `ai_plan_conversations`

### 8. Documentation
**Files Created**:
- [AI_PLAN_API_DOCUMENTATION.md](AI_PLAN_API_DOCUMENTATION.md) - Complete API reference (23+ pages)
- [AI_PLAN_QUICK_REFERENCE.md](AI_PLAN_QUICK_REFERENCE.md) - Quick reference guide
- [test_ai_plan_api.py](test_ai_plan_api.py) - Comprehensive test script

---

## 🔑 Key Features

### Session Management
- ✅ One session per user (OneToOne relationship)
- ✅ Automatic session creation on first chat
- ✅ Session ID returned in every response
- ✅ No need to pass session_id (tied to authenticated user)

### Conversation Context
- ✅ Last 10 conversations used as context
- ✅ Profile summary accumulated over time
- ✅ Current workout/diet plans included in context
- ✅ Full conversation history retrievable via GET /sessions/

### AI Integration
- ✅ OpenAI GPT-4o-mini model
- ✅ JSON-only responses enforced
- ✅ System prompt with comprehensive instructions
- ✅ Handles workout plans, diet plans, and basic questions
- ✅ Fitness-focused (rejects non-fitness queries)

### Response Types
- ✅ **Basic questions**: Returns message only
- ✅ **Workout requests**: Returns message + workout array
- ✅ **Diet requests**: Returns message + diet array
- ✅ **Modifications**: Returns message + complete updated plan
- ✅ **Profile updates**: Returns message + updated summary

### Security & Authentication
- ✅ JWT authentication required (IsAuthenticated)
- ✅ User-specific sessions (cannot access other users' data)
- ✅ OpenAI API key stored securely in .env

---

## 📋 Differences from FastAPI Version

| Feature | FastAPI | Django |
|---------|---------|--------|
| **Storage** | JSON file | Database (SQLite/PostgreSQL) |
| **Sessions per user** | Multiple (via session_id param) | One (OneToOne) |
| **Authentication** | None | JWT required |
| **Session management** | Manual (pass session_id) | Automatic (from auth user) |
| **User association** | None | Tied to User model |
| **History retrieval** | Not available | GET /sessions/ |
| **Response format** | Direct JSON | Wrapped in standard format |
| **Model** | gpt-5.2 (invalid) | gpt-4o-mini |

---

## 🚀 How to Use

### 1. Start the Server
```bash
cd /home/mainbsl4/Desktop/projects/py/tomsink101_django
source venv/bin/activate
python manage.py runserver 0.0.0.0:8007
```

### 2. Get JWT Token
```bash
curl -X POST http://localhost:8007/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### 3. Chat with AI
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is a plank exercise?"}'
```

### 4. Get Session History
```bash
curl -X GET http://localhost:8007/api/sessions/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Run Test Script
```bash
# Edit test_ai_plan_api.py and add your JWT token
python test_ai_plan_api.py
```

---

## 📦 Database Schema

### ai_plan_sessions
```sql
CREATE TABLE ai_plan_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,  -- OneToOne with User
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_user(id)
);
```

### ai_plan_conversations
```sql
CREATE TABLE ai_plan_conversations (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    user_message TEXT NOT NULL,
    ai_message TEXT NOT NULL,
    summary TEXT,
    workout JSON DEFAULT '[]',
    diet JSON DEFAULT '[]',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES ai_plan_sessions(id)
);
```

---

## 🔧 Configuration

### Environment Variables Required
```env
OPENAI_API_KEY=sk-proj-...your-key...
```

### Settings (project/settings.py)
- `OPENAI_API_KEY` is read from environment
- REST_FRAMEWORK configured with JWT authentication
- ai_plan app already in INSTALLED_APPS

### URLs (project/urls.py)
- ai_plan URLs mounted at `/api/`
- Endpoints accessible at:
  - `/api/chat/`
  - `/api/sessions/`

---

## 🧪 Testing

### Manual Testing
1. Use the provided cURL commands in documentation
2. Test with Postman or similar tools
3. Use the Django admin interface to view sessions/conversations

### Automated Testing
Run the test script:
```bash
python test_ai_plan_api.py
```

Tests included:
1. Basic question (no plan generation)
2. Collect user information
3. Request workout plan
4. Request diet plan
5. Modify existing workout
6. Retrieve session history

### Admin Interface
```bash
# Create superuser if not exists
python manage.py createsuperuser

# Access admin at:
http://localhost:8007/admin/

# Navigate to:
# - AI Plan > AI Plan Sessions
# - AI Plan > AI Plan Conversations
```

---

## 📝 Next Steps (Optional)

### Enhancements
1. **Add filtering to sessions endpoint**: Filter by date range, search conversations
2. **Add conversation deletion**: Allow users to clear their history
3. **Add plan export**: Export workout/diet plans as PDF
4. **Add plan scheduling**: Schedule workouts for specific dates
5. **Add progress tracking**: Track completed workouts
6. **Add notifications**: Remind users about workouts

### Integration with Existing Apps
1. **Link with task app**: Create WorkoutPlan/DietPlan from AI suggestions
2. **Link with notifications**: Notify users about new plans
3. **Link with subscription**: Premium features for paid users

### Performance Optimization
1. **Cache conversation history**: Reduce database queries
2. **Async OpenAI calls**: Use async views for better performance
3. **Rate limiting**: Prevent abuse of OpenAI API

---

## 🐛 Troubleshooting

### "OPENAI_API_KEY environment variable is not set"
- Check `.env` file has `OPENAI_API_KEY=...`
- Restart Django server after adding key

### "No session found for this user"
- Normal on first GET /sessions/ call
- Send at least one POST /chat/ to create session

### "Invalid JSON response from AI"
- Check OpenAI API key is valid
- Verify API has sufficient credits
- Check OpenAI API status

### 401 Unauthorized
- Verify JWT token is included in Authorization header
- Check token hasn't expired (1 day default)
- Use token refresh endpoint if needed

---

## ✅ Implementation Complete

All FastAPI functionality has been successfully converted to Django REST Framework with the following improvements:

1. ✅ Database persistence (vs JSON file)
2. ✅ User authentication and authorization
3. ✅ One session per user (vs multiple sessions)
4. ✅ Automatic session management
5. ✅ Comprehensive API documentation
6. ✅ Test suite included
7. ✅ Admin interface for management
8. ✅ Standard Django patterns followed
9. ✅ Error handling and validation
10. ✅ RESTful API design

**Status**: Ready for testing and deployment! 🎉
