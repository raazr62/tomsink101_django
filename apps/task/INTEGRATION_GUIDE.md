# AI Fitness Tracker - Complete Integration Guide

## Overview
This guide explains how the AI chat system integrates with the task tracking system to create a complete fitness tracking solution.

## System Flow

### 1. User Interacts with AI (`/api/ai/chat/`)
```
User → AI Chat → WorkoutPlan + DietPlan → Task Tracking → Progress Tracking
```

### 2. Data Flow Diagram
```
┌─────────────────┐
│   User Input    │
│  "Create a      │
│  workout plan"  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Chat API   │
│ /api/ai/chat/   │
└────────┬────────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│  ChatSession    │      │   ChatMessage   │
│  ChatMessage    │      │   (stores AI    │
│  (conversation) │      │    response)    │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Auto-Create     │
│ WorkoutPlan +   │
│ DietPlan        │
└────────┬────────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│  WorkoutPlan    │      │   DietPlan      │
│  + Exercise[]   │      │   + Meal[]      │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │                        │
         ▼                        ▼
┌──────────────────────────────────────┐
│         User Tracks Progress         │
│   - Mark exercises complete          │
│   - Mark meals complete              │
│   - View calendar                    │
└────────┬─────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ DailyProgress   │
│ (automatic log) │
└─────────────────┘
```

## API Endpoints & Their Relationships

### AI Chat System (manageai app)

#### 1. POST `/api/ai/chat/`
**Purpose**: Send message to AI and get workout/diet plans

**Request**:
```json
{
  "user_input": "Create me a workout plan",
  "session_id": "optional-uuid"
}
```

**Response**:
```json
{
  "status": 200,
  "success": true,
  "message": "AI response generated successfully",
  "data": {
    "session_id": "uuid-of-chat-session",
    "message": "I've created a personalized workout plan for you...",
    "workout": [
      {"exercise": "Push-ups", "sets": 3, "reps": "10-12"},
      {"exercise": "Squats", "sets": 4, "reps": "15"}
    ],
    "diet": [
      {
        "meal": "Breakfast",
        "title": "Protein-Rich Morning",
        "items": ["Eggs", "Oatmeal", "Banana"],
        "nutrients": {"calories": 450, "protein": 30, "carbs": 55, "fats": 12}
      }
    ],
    "summary": "Male, 25 years, 75kg, intermediate level...",
    "workout_plan_id": "uuid-of-created-workout-plan",
    "diet_plan_id": "uuid-of-created-diet-plan"
  }
}
```

**What Happens Internally**:
1. Saves user message to `ChatMessage`
2. Calls OpenAI API with conversation history
3. Parses AI response for workout/diet data
4. **Automatically creates** `WorkoutPlan` with `Exercise` records
5. **Automatically creates** `DietPlan` with `Meal` records
6. Both plans are set to `status='active'`
7. Both plans are linked to the `ChatSession` via `chat_session` foreign key

---

### Task Tracking System (task app)

#### 2. GET `/api/tasks/dashboard/`
**Purpose**: Get overview of all active plans and today's progress

**Response**:
```json
{
  "active_workout_plan": {
    "id": "uuid",
    "name": "Workout Plan - 2025-01-15",
    "progress_percentage": 35.5,
    "total_exercises": 8,
    "completed_exercises": 3
  },
  "active_diet_plan": {
    "id": "uuid",
    "name": "Diet Plan - 2025-01-15",
    "total_daily_calories": 2100,
    "total_meals": 4
  },
  "today_progress": {
    "date": "2025-11-18",
    "exercises_completed": 3,
    "meals_completed": 2
  }
}
```

---

#### 3. GET `/api/tasks/weekly-stats/`
**Purpose**: Get statistics for the top 4 cards in UI

**Response**:
```json
{
  "calories_burned": 2450,
  "calories_burned_change": "+12%",
  "nutrition": 14200,
  "nutrition_change": "+15%",
  "active_time": 5.25,
  "active_time_change": "+1.2h",
  "workouts_completed": 7,
  "workouts_completed_change": "+3",
  "week_progress": 65
}
```

**What Happens Internally**:
- Calculates current week's date range
- Aggregates `DailyProgress` records for the week
- Sums up exercises and meals completed
- Calculates nutrition from completed meals (status='completed')

---

#### 4. GET `/api/tasks/calendar/?year=2025&month=11`
**Purpose**: Get calendar data showing workout completion status per day

**Response**:
```json
{
  "year": 2025,
  "month": 11,
  "month_name": "November 2025",
  "days": [
    {
      "day": 1,
      "date": "2025-11-01",
      "status": "complete",
      "exercises_completed": 8,
      "meals_completed": 4
    },
    {
      "day": 2,
      "date": "2025-11-02",
      "status": "incomplete",
      "exercises_completed": 3,
      "meals_completed": 2
    },
    {
      "day": 3,
      "date": "2025-11-03",
      "status": "rest",
      "exercises_completed": 0,
      "meals_completed": 0
    }
  ]
}
```

**Status Types**:
- `complete`: All exercises and meals completed
- `incomplete`: Some exercises or meals completed
- `rest`: No activity

**What Happens Internally**:
- Gets active `WorkoutPlan` and `DietPlan`
- Queries `DailyProgress` for the specified month
- Compares actual completion vs expected (total exercises/meals)

---

#### 5. GET `/api/tasks/daily/2025-11-18/`
**Purpose**: Get detailed workout and diet information for a specific date

**Response**:
```json
{
  "date": "2025-11-18",
  "workout_plan": {
    "id": "uuid",
    "name": "Workout Plan - 2025-01-15",
    "exercises": [
      {
        "id": "uuid",
        "name": "Push-ups",
        "sets": 3,
        "reps": "10-12",
        "completed_sets": 2,
        "status": "in_progress",
        "completion_percentage": 66.67,
        "order": 0
      },
      {
        "id": "uuid",
        "name": "Squats",
        "sets": 4,
        "reps": "15",
        "completed_sets": 4,
        "status": "completed",
        "completion_percentage": 100,
        "order": 1
      }
    ],
    "total_exercises": 8,
    "completed_exercises": 3,
    "progress_percentage": 37.5
  },
  "diet_plan": {
    "id": "uuid",
    "name": "Diet Plan - 2025-01-15",
    "meals": [
      {
        "id": "uuid",
        "meal_type": "breakfast",
        "title": "Protein-Rich Morning",
        "items": ["Eggs", "Oatmeal", "Banana"],
        "calories": 450,
        "protein": 30,
        "carbs": 55,
        "fats": 12,
        "status": "completed",
        "order": 0
      }
    ],
    "total_meals": 4,
    "completed_meals": 2,
    "nutrition_totals": {
      "calories": 950,
      "protein": 65,
      "carbs": 120,
      "fats": 28
    },
    "target_nutrition": {
      "calories": 2100,
      "protein": 150,
      "carbs": 250,
      "fats": 70
    }
  },
  "daily_progress": {
    "date": "2025-11-18",
    "exercises_completed": 3,
    "meals_completed": 2
  }
}
```

**What Happens Internally**:
- Gets active `WorkoutPlan` and `DietPlan` for the user
- Retrieves all exercises with their completion status
- Retrieves all meals with their completion status
- Calculates nutrition totals from completed meals only
- Gets `DailyProgress` record for the specific date

---

#### 6. POST `/api/tasks/exercises/{exercise_id}/toggle-set/`
**Purpose**: Mark individual sets as complete for an exercise

**Request**:
```json
{
  "set_number": 2
}
```

**Response**:
```json
{
  "id": "uuid",
  "completed_sets": 2,
  "status": "in_progress",
  "completion_percentage": 66.67
}
```

**What Happens Internally**:
1. Toggles the set completion for the exercise
2. Updates exercise status:
   - `pending`: 0 sets completed
   - `in_progress`: Some sets completed
   - `completed`: All sets completed
3. **Automatically updates** `DailyProgress`:
   - Creates or updates today's progress record
   - Counts completed exercises in the workout plan
   - Links to active `WorkoutPlan` and `DietPlan`

---

#### 7. POST `/api/tasks/meals/{meal_id}/toggle/`
**Purpose**: Toggle meal completion status

**Response**:
```json
{
  "id": "uuid",
  "status": "completed",
  "is_completed": true
}
```

**What Happens Internally**:
1. Toggles meal status between `pending` and `completed`
2. **Automatically updates** `DailyProgress`:
   - Creates or updates today's progress record
   - Counts completed meals in the diet plan
   - Links to active `WorkoutPlan` and `DietPlan`

---

## Database Relationships

### Foreign Key Relationships
```
User
├── ChatSession (multiple)
│   ├── ChatMessage (multiple)
│   ├── WorkoutPlan (multiple)
│   └── DietPlan (multiple)
│
├── WorkoutPlan (multiple)
│   ├── Exercise (multiple)
│   └── DailyProgress (multiple)
│
├── DietPlan (multiple)
│   ├── Meal (multiple)
│   └── DailyProgress (multiple)
│
└── DailyProgress (multiple)
    ├── Links to WorkoutPlan (optional)
    └── Links to DietPlan (optional)
```

### Key Model Fields

**WorkoutPlan**:
- `user`: Who owns this plan
- `chat_session`: Which AI conversation created it
- `status`: active/completed/paused
- Properties: `total_exercises`, `completed_exercises`, `progress_percentage`

**Exercise**:
- `workout_plan`: Which plan this belongs to
- `completed_sets`: How many sets done
- `status`: pending/in_progress/completed/skipped
- Property: `completion_percentage`

**DietPlan**:
- `user`: Who owns this plan
- `chat_session`: Which AI conversation created it
- `status`: active/completed/paused
- Properties: `total_daily_calories`, `total_daily_protein`, etc.

**Meal**:
- `diet_plan`: Which plan this belongs to
- `meal_type`: breakfast/lunch/snack/dinner
- `status`: pending/completed/skipped
- `items`: JSON array of food items

**DailyProgress**:
- `user`: Who this progress belongs to
- `date`: The specific date (unique per user per date)
- `workout_plan`: Current active workout plan
- `diet_plan`: Current active diet plan
- `exercises_completed`: Count of completed exercises
- `meals_completed`: Count of completed meals

---

## Complete User Journey Example

### Step 1: User Chats with AI
```http
POST /api/ai/chat/
Authorization: Bearer <JWT_TOKEN>

{
  "user_input": "Create me a workout plan for muscle gain"
}
```

**Result**: 
- Creates `ChatSession` and `ChatMessage`
- AI generates workout and diet plans
- **Automatically creates**:
  - `WorkoutPlan` (status='active') with 8 `Exercise` records
  - `DietPlan` (status='active') with 4 `Meal` records

---

### Step 2: User Views Dashboard
```http
GET /api/tasks/dashboard/
Authorization: Bearer <JWT_TOKEN>
```

**Result**: Shows the newly created active plans

---

### Step 3: User Views Calendar
```http
GET /api/tasks/calendar/?year=2025&month=11
Authorization: Bearer <JWT_TOKEN>
```

**Result**: Shows month view with rest days (no progress yet)

---

### Step 4: User Clicks on Today's Date
```http
GET /api/tasks/daily/2025-11-18/
Authorization: Bearer <JWT_TOKEN>
```

**Result**: Shows all exercises and meals for today

---

### Step 5: User Completes First Set of Push-ups
```http
POST /api/tasks/exercises/{exercise_id}/toggle-set/
Authorization: Bearer <JWT_TOKEN>

{
  "set_number": 1
}
```

**Result**: 
- Exercise `completed_sets` = 1
- Exercise `status` = "in_progress"
- **Automatically creates** `DailyProgress` for today

---

### Step 6: User Completes All Sets
```http
POST /api/tasks/exercises/{exercise_id}/toggle-set/
(repeat for sets 2, 3)
```

**Result**: 
- Exercise `completed_sets` = 3
- Exercise `status` = "completed"
- **Updates** `DailyProgress.exercises_completed` = 1

---

### Step 7: User Marks Breakfast Complete
```http
POST /api/tasks/meals/{meal_id}/toggle/
Authorization: Bearer <JWT_TOKEN>
```

**Result**: 
- Meal `status` = "completed"
- **Updates** `DailyProgress.meals_completed` = 1

---

### Step 8: User Checks Weekly Stats
```http
GET /api/tasks/weekly-stats/
Authorization: Bearer <JWT_TOKEN>
```

**Result**: Shows aggregated stats for the week

---

### Step 9: User Checks Calendar Again
```http
GET /api/tasks/calendar/?year=2025&month=11
Authorization: Bearer <JWT_TOKEN>
```

**Result**: Today shows "incomplete" status (some progress made)

---

## Important Notes

### Automatic Task Creation
✅ When AI generates workout/diet plans, they are **automatically** saved as trackable tasks
✅ No separate API call needed to create tasks
✅ Plans are immediately available in `/api/tasks/dashboard/`

### Progress Tracking
✅ `DailyProgress` is **automatically** created/updated when:
  - User marks exercise sets complete
  - User marks meals complete
✅ Only one `DailyProgress` record per user per date
✅ Always links to currently active `WorkoutPlan` and `DietPlan`

### Plan Status
- `active`: Currently being tracked (only one workout and one diet plan should be active)
- `completed`: Finished
- `paused`: Temporarily stopped

### Data Integrity
- All plans link back to the `ChatSession` that created them
- Exercise/Meal completion is tracked individually
- Calendar calculations use active plans only
- Weekly stats aggregate from `DailyProgress` records

---

## Frontend Integration Tips

### Dashboard Page
1. Call `/api/tasks/dashboard/` to get overview
2. Call `/api/tasks/weekly-stats/` for top cards
3. Call `/api/tasks/calendar/` for calendar widget

### Calendar Click
1. When user clicks a date, call `/api/tasks/daily/{date}/`
2. Display exercises with set-by-set tracking
3. Display meals with complete/incomplete status

### Exercise Tracking
1. For each exercise, show sets as individual buttons/checkboxes
2. When user completes a set, call `/api/tasks/exercises/{id}/toggle-set/`
3. UI automatically updates from response

### Meal Tracking
1. For each meal card, show complete/replace buttons
2. When user clicks complete, call `/api/tasks/meals/{id}/toggle/`
3. Nutrition totals update automatically

---

## Testing the Complete Flow

### 1. Create Plans via AI
```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Create me a workout plan"
  }'
```

### 2. View Dashboard
```bash
curl -X GET http://localhost:8000/api/tasks/dashboard/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. View Today's Workout
```bash
curl -X GET http://localhost:8000/api/tasks/daily/2025-11-18/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Complete a Set
```bash
curl -X POST http://localhost:8000/api/tasks/exercises/EXERCISE_ID/toggle-set/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"set_number": 1}'
```

### 5. Check Progress
```bash
curl -X GET http://localhost:8000/api/tasks/calendar/?year=2025&month=11 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Summary

✅ AI Chat creates trackable workout and diet plans automatically
✅ All plans are linked to the chat session that created them
✅ Users can track progress set-by-set for exercises
✅ Users can mark meals complete/incomplete
✅ Daily progress is tracked automatically
✅ Calendar shows completion status per day
✅ Weekly stats aggregate all progress
✅ Everything is linked through proper foreign key relationships
