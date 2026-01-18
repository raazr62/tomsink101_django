# AI Plan API - Architecture & Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Frontend)                     │
│                     React / Mobile App                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ JWT Token
                             │ POST /api/chat/
                             │ GET /api/sessions/
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django REST Framework                     │
│                                                               │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │  Authentication │◄────────┤   JWT Middleware │            │
│  │     Required    │         │                  │            │
│  └────────┬────────┘         └──────────────────┘            │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────┐             │
│  │           AI Plan Views                     │             │
│  │                                             │             │
│  │  • AIPlanChatView (POST)                   │             │
│  │    - Validate request                      │             │
│  │    - Get/create session                    │             │
│  │    - Build conversation history            │             │
│  │    - Call OpenAI API                       │             │
│  │    - Save conversation                     │             │
│  │                                             │             │
│  │  • SessionDetailView (GET)                 │             │
│  │    - Retrieve user session                 │             │
│  │    - Return conversation history           │             │
│  └──────────────┬──────────────────────────────┘             │
│                 │                                             │
└─────────────────┼─────────────────────────────────────────────┘
                  │
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────────┐
│   Database   │    │   OpenAI API     │
│              │    │                  │
│ • sessions   │    │  gpt-4o-mini     │
│ • convos     │    │  JSON responses  │
└──────────────┘    └──────────────────┘
```

---

## Request Flow

### Chat Request Flow

```
1. Client sends POST /api/chat/
   {
     "user_input": "Create workout plan",
     "summary": "Male, 25, 80kg",
     "workout": [...],
     "diet": [...]
   }
   + Authorization: Bearer <token>

2. Django JWT Middleware validates token
   → Identifies User

3. AIPlanChatView.post()
   │
   ├─► Validate request data (AskRequestSerializer)
   │
   ├─► Get or create AIPlanSession for user
   │   (OneToOne, so each user has 1 session)
   │
   ├─► Build conversation history
   │   SELECT * FROM conversations
   │   WHERE session_id = user.session.id
   │   ORDER BY created_at DESC
   │   LIMIT 10
   │
   ├─► Format system prompt with:
   │   • User profile summary
   │   • Current workout plan
   │   • Current diet plan
   │   • User input
   │   • Conversation history
   │
   ├─► Call OpenAI API
   │   client.chat.completions.create(
   │     model="gpt-4o-mini",
   │     messages=[...],
   │     response_format={"type": "json_object"}
   │   )
   │
   ├─► Parse JSON response
   │   {
   │     "message": "...",
   │     "workout": [...],
   │     "diet": [...],
   │     "summary": "..."
   │   }
   │
   ├─► Save conversation to database
   │   INSERT INTO conversations
   │   (session_id, user_message, ai_message,
   │    summary, workout, diet)
   │
   └─► Return response
       {
         "status": 200,
         "success": true,
         "data": {
           "session_id": "...",
           "response": {...}
         }
       }
```

### Session Retrieval Flow

```
1. Client sends GET /api/sessions/
   + Authorization: Bearer <token>

2. Django JWT Middleware validates token
   → Identifies User

3. SessionDetailView.get()
   │
   ├─► Query user's session
   │   SELECT * FROM sessions
   │   WHERE user_id = user.id
   │
   ├─► Query all conversations
   │   SELECT * FROM conversations
   │   WHERE session_id = session.id
   │   ORDER BY created_at DESC
   │
   ├─► Serialize data (SessionDetailSerializer)
   │
   └─► Return response
       {
         "status": 200,
         "success": true,
         "data": {
           "id": "...",
           "conversations": [...]
         }
       }
```

---

## Database Relationships

```
┌─────────────────────┐
│      User           │
│  (Django Auth)      │
│                     │
│  • id (PK)          │
│  • email            │
│  • password         │
│  • ...              │
└──────────┬──────────┘
           │
           │ OneToOne
           │
           ▼
┌─────────────────────┐
│   AIPlanSession     │
│                     │
│  • id (UUID, PK)    │
│  • user_id (FK)     │◄────── OneToOne with User
│  • created_at       │
│  • updated_at       │
└──────────┬──────────┘
           │
           │ One-to-Many
           │
           ▼
┌─────────────────────┐
│ AIPlanConversation  │
│                     │
│  • id (UUID, PK)    │
│  • session_id (FK)  │◄────── Many conversations per session
│  • user_message     │
│  • ai_message       │
│  • summary          │
│  • workout (JSON)   │
│  • diet (JSON)      │
│  • created_at       │
│  • updated_at       │
└─────────────────────┘

Relationships:
• 1 User ←→ 1 Session (OneToOne)
• 1 Session ←→ Many Conversations (ForeignKey)
```

---

## Data Flow Examples

### Example 1: First-time User

```
Step 1: User logs in
  POST /api/login/
  ← Returns JWT token

Step 2: First chat message
  POST /api/chat/
  Body: {"user_input": "I want to lose weight"}
  
  Actions:
  1. No session exists → Create new AIPlanSession
  2. No conversation history → Empty context
  3. Call OpenAI with minimal context
  4. Save first conversation
  5. Return session_id + response

Step 3: Follow-up message
  POST /api/chat/
  Body: {
    "user_input": "I'm 25 years old, 100kg",
    "summary": "Goal: lose weight"
  }
  
  Actions:
  1. Session exists → Use existing AIPlanSession
  2. Load previous conversation(s)
  3. Call OpenAI with full context
  4. Save new conversation
  5. Return updated summary

Step 4: Request plan
  POST /api/chat/
  Body: {
    "user_input": "Create workout plan",
    "summary": "Goal: lose weight; Age: 25; Weight: 100kg"
  }
  
  Actions:
  1. Use existing session
  2. Load conversation history (includes previous 2 messages)
  3. Call OpenAI with full context
  4. AI generates workout array
  5. Save conversation with workout data
  6. Return workout plan
```

### Example 2: Returning User

```
User logs in again (next day)
  POST /api/login/
  ← Returns new JWT token

Check previous conversations
  GET /api/sessions/
  
  Actions:
  1. Find existing AIPlanSession for user
  2. Load all conversations
  3. Return full history

Continue previous conversation
  POST /api/chat/
  Body: {
    "user_input": "Modify workout - add more cardio",
    "summary": "Goal: lose weight; Age: 25; Weight: 100kg",
    "workout": [...previous workout...]
  }
  
  Actions:
  1. Use existing session (still only 1 per user)
  2. Load last 10 conversations as context
  3. Include previous workout in prompt
  4. AI generates updated workout
  5. Save new conversation
  6. Return modified workout
```

---

## Context Building

### How Context is Built for OpenAI

```python
# 1. Get last 10 conversations
conversations = session.conversations.all()[:10]

# 2. Build history string
conversation_history = ""
for conv in reversed(conversations):
    conversation_history += f"User: {conv.user_message}\n"
    conversation_history += f"AI: {conv.ai_message}\n\n"

# 3. Format system prompt
prompt = SYSTEM_PROMPT.format(
    summary=request.summary or "No profile info",
    workout=json.dumps(request.workout) or "No workout plan",
    diet=json.dumps(request.diet) or "No diet plan",
    user_input=request.user_input,
    conversation_history=conversation_history or "No previous conversation"
)

# 4. Send to OpenAI
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": prompt}],
    temperature=0.7,
    response_format={"type": "json_object"}
)
```

---

## Security Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. Login
       ▼
┌─────────────────────────┐
│  POST /api/login/       │
│  {"email", "password"}  │
└──────┬──────────────────┘
       │
       │ 2. Django validates credentials
       ▼
┌─────────────────────────┐
│  JWT Token Generated    │
│  • Access token (1 day) │
│  • Refresh token        │
└──────┬──────────────────┘
       │
       │ 3. Return tokens
       ▼
┌─────────────┐
│   Client    │
│  Stores JWT │
└──────┬──────┘
       │
       │ 4. Use API with token
       │    Authorization: Bearer <token>
       ▼
┌─────────────────────────┐
│  POST /api/chat/        │
│  + Authorization header │
└──────┬──────────────────┘
       │
       │ 5. JWT Middleware validates token
       │    • Check signature
       │    • Check expiration
       │    • Extract user_id
       ▼
┌─────────────────────────┐
│  request.user = User    │
│  (Authenticated)        │
└──────┬──────────────────┘
       │
       │ 6. View checks permission
       │    IsAuthenticated
       ▼
┌─────────────────────────┐
│  Process request        │
│  • Get user's session   │
│  • User can only access │
│    their own data       │
└─────────────────────────┘
```

---

## Error Handling Flow

```
Request → Validation → Authentication → Processing → Response
   │          │             │              │
   │          │             │              ├─► Success (200)
   │          │             │              └─► Server Error (500)
   │          │             │
   │          │             └─► Auth Failed (401)
   │          │
   │          └─► Validation Failed (400)
   │
   └─► Missing Token (401)
```

---

## Comparison: FastAPI vs Django

### FastAPI Version
```
Request
  ↓
FastAPI endpoint (no auth)
  ↓
Load JSON file (workout_history.json)
  ↓
Find/create session by session_id
  ↓
Build context from file data
  ↓
Call OpenAI
  ↓
Save to JSON file
  ↓
Return response
```

### Django Version
```
Request
  ↓
JWT Authentication
  ↓
Permission Check (IsAuthenticated)
  ↓
Django REST View
  ↓
Query Database (get user's session)
  ↓
Build context from DB
  ↓
Call OpenAI
  ↓
Save to Database
  ↓
Return standardized response
```

**Key Improvements:**
- ✅ Database instead of file storage
- ✅ User authentication and isolation
- ✅ One session per user (automatic)
- ✅ Relational data (easy querying)
- ✅ RESTful API design
- ✅ Standard error handling
- ✅ Admin interface included

---

## Performance Considerations

### Database Queries
```python
# Optimized query with select_related
session = AIPlanSession.objects.select_related('user').get(user=request.user)
conversations = session.conversations.all()[:10]

# Result: 2 queries total
# 1. Get session + user (JOIN)
# 2. Get last 10 conversations
```

### Caching Opportunities
```python
# Cache conversation history for 5 minutes
from django.core.cache import cache

cache_key = f'ai_plan_history_{session.id}'
conversation_history = cache.get(cache_key)

if not conversation_history:
    # Build from database
    conversation_history = build_history(session)
    cache.set(cache_key, conversation_history, 300)  # 5 min
```

### Rate Limiting
```python
# Optional: Add rate limiting to prevent API abuse
from rest_framework.throttling import UserRateThrottle

class AIPlanChatView(APIView):
    throttle_classes = [UserRateThrottle]
    # Allow 10 requests per minute per user
```

---

## Summary

The Django implementation provides:
1. **Secure**: JWT authentication, user isolation
2. **Scalable**: Database storage, efficient queries
3. **Maintainable**: Standard Django patterns, admin interface
4. **Feature-rich**: Session history, conversation context
5. **Well-documented**: Complete API docs, test suite

**Ready for production deployment! 🚀**
