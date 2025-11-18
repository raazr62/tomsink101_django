# Task Management System - API Documentation

## Overview

The Task Management System automatically saves AI-generated workout and diet plans as trackable tasks. Users can monitor their progress, mark exercises and meals as completed, and track their fitness journey.

---

## Base URL
All task endpoints are prefixed with `/api/tasks/`

## Authentication
All endpoints require JWT authentication.

---

## Features

### ✅ Automatic Task Creation
- When AI generates a workout plan → Automatically creates WorkoutPlan with Exercises
- When AI generates a diet plan → Automatically creates DietPlan with Meals
- Plans are linked to the chat session for reference

### ✅ Progress Tracking
- Track completed exercises and sets
- Mark meals as completed
- View overall progress percentage
- Daily progress logging

### ✅ Status Management
- **Workout Plans**: Active, Completed, Paused
- **Exercises**: Pending, In Progress, Completed, Skipped
- **Diet Plans**: Active, Completed, Paused
- **Meals**: Pending, Completed, Skipped

---

## API Endpoints

### 1. Dashboard Overview
**Endpoint:** `GET /api/tasks/dashboard/`

**Description:** Get an overview of active plans and today's progress.

**Response:**
```json
{
  "active_workout_plan": {
    "id": "uuid",
    "name": "Workout Plan - 2024-01-01",
    "summary": "Male, 23 years old, 80kg, beginner...",
    "status": "active",
    "progress_percentage": 25.5,
    "total_exercises": 6,
    "completed_exercises": 2,
    "exercises": [
      {
        "id": "uuid",
        "name": "Push-ups",
        "sets": 3,
        "reps": "10-15",
        "completed_sets": 2,
        "status": "in_progress",
        "completion_percentage": 66.67
      }
    ]
  },
  "active_diet_plan": {
    "id": "uuid",
    "name": "Diet Plan - 2024-01-01",
    "summary": "Male, 23 years old, 80kg, beginner...",
    "status": "active",
    "total_meals": 4,
    "total_daily_calories": 2000,
    "total_daily_protein": 150,
    "total_daily_carbs": 250,
    "total_daily_fats": 55,
    "meals": [
      {
        "id": "uuid",
        "meal_type": "breakfast",
        "title": "High-Protein Oatmeal",
        "items": ["Oats", "Almond Milk", "Protein Powder", "Berries"],
        "calories": 350,
        "protein": 25,
        "carbs": 45,
        "fats": 8,
        "status": "completed"
      }
    ]
  },
  "today_progress": {
    "date": "2024-01-01",
    "exercises_completed": 2,
    "meals_completed": 3
  },
  "total_workout_plans": 5,
  "total_diet_plans": 5
}
```

---

### 2. List Workout Plans
**Endpoint:** `GET /api/tasks/workout-plans/`

**Description:** Get all workout plans for the authenticated user.

**Response:**
```json
[
  {
    "id": "uuid",
    "user": 1,
    "name": "Workout Plan - 2024-01-01",
    "summary": "Weight loss plan for beginner",
    "status": "active",
    "start_date": "2024-01-01",
    "target_completion_date": null,
    "progress_percentage": 33.33,
    "total_exercises": 6,
    "completed_exercises": 2,
    "exercises": [...]
  }
]
```

---

### 3. Get Workout Plan Details
**Endpoint:** `GET /api/tasks/workout-plans/<plan_id>/`

**Description:** Get detailed information about a specific workout plan.

**Response:**
```json
{
  "id": "uuid",
  "name": "Workout Plan - 2024-01-01",
  "summary": "Male, 23 years old...",
  "status": "active",
  "exercises": [
    {
      "id": "uuid",
      "name": "Jumping Jacks",
      "sets": 3,
      "reps": "20-30",
      "completed_sets": 0,
      "notes": "",
      "status": "pending",
      "order": 0,
      "completion_percentage": 0
    },
    {
      "id": "uuid",
      "name": "Push-ups",
      "sets": 3,
      "reps": "8-10",
      "completed_sets": 2,
      "notes": "Getting easier!",
      "status": "in_progress",
      "order": 1,
      "completion_percentage": 66.67
    }
  ],
  "progress_percentage": 25.0
}
```

---

### 4. Update Workout Plan
**Endpoint:** `PATCH /api/tasks/workout-plans/<plan_id>/`

**Description:** Update workout plan details.

**Request Body:**
```json
{
  "name": "My Custom Workout Plan",
  "status": "completed",
  "target_completion_date": "2024-03-01"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "My Custom Workout Plan",
  "status": "completed",
  ...
}
```

---

### 5. Delete Workout Plan
**Endpoint:** `DELETE /api/tasks/workout-plans/<plan_id>/`

**Description:** Delete a workout plan and all its exercises.

**Response:**
```json
{
  "message": "Workout plan deleted successfully"
}
```

---

### 6. Update Exercise Progress
**Endpoint:** `PATCH /api/tasks/exercises/<exercise_id>/`

**Description:** Update exercise completion status and sets.

**Request Body:**
```json
{
  "completed_sets": 3,
  "status": "completed",
  "notes": "Felt great today!"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Push-ups",
  "sets": 3,
  "reps": "10-15",
  "completed_sets": 3,
  "notes": "Felt great today!",
  "status": "completed",
  "completion_percentage": 100
}
```

---

### 7. List Diet Plans
**Endpoint:** `GET /api/tasks/diet-plans/`

**Description:** Get all diet plans for the authenticated user.

**Response:**
```json
[
  {
    "id": "uuid",
    "user": 1,
    "name": "Diet Plan - 2024-01-01",
    "summary": "Weight loss diet plan",
    "status": "active",
    "total_meals": 4,
    "total_daily_calories": 2000,
    "total_daily_protein": 150,
    "meals": [...]
  }
]
```

---

### 8. Get Diet Plan Details
**Endpoint:** `GET /api/tasks/diet-plans/<plan_id>/`

**Description:** Get detailed information about a specific diet plan.

**Response:**
```json
{
  "id": "uuid",
  "name": "Diet Plan - 2024-01-01",
  "summary": "Balanced diet for weight loss",
  "status": "active",
  "meals": [
    {
      "id": "uuid",
      "meal_type": "breakfast",
      "title": "High-Protein Oatmeal",
      "items": ["Oats", "Almond Milk", "Protein Powder", "Berries"],
      "calories": 350,
      "protein": 25,
      "carbs": 45,
      "fats": 8,
      "notes": "",
      "status": "completed",
      "order": 0
    },
    {
      "id": "uuid",
      "meal_type": "lunch",
      "title": "Grilled Chicken Salad",
      "items": ["Grilled Chicken", "Mixed Greens", "Tomatoes", "Olive Oil"],
      "calories": 400,
      "protein": 35,
      "carbs": 20,
      "fats": 18,
      "notes": "",
      "status": "pending",
      "order": 1
    }
  ],
  "total_daily_calories": 2000,
  "total_daily_protein": 150,
  "total_daily_carbs": 250,
  "total_daily_fats": 55
}
```

---

### 9. Update Diet Plan
**Endpoint:** `PATCH /api/tasks/diet-plans/<plan_id>/`

**Description:** Update diet plan details.

**Request Body:**
```json
{
  "name": "My Custom Diet Plan",
  "status": "active"
}
```

---

### 10. Delete Diet Plan
**Endpoint:** `DELETE /api/tasks/diet-plans/<plan_id>/`

**Description:** Delete a diet plan and all its meals.

---

### 11. Update Meal Status
**Endpoint:** `PATCH /api/tasks/meals/<meal_id>/`

**Description:** Mark a meal as completed or add notes.

**Request Body:**
```json
{
  "status": "completed",
  "notes": "Delicious and filling!"
}
```

**Response:**
```json
{
  "id": "uuid",
  "meal_type": "breakfast",
  "title": "High-Protein Oatmeal",
  "items": ["Oats", "Almond Milk", "Protein Powder", "Berries"],
  "calories": 350,
  "protein": 25,
  "carbs": 45,
  "fats": 8,
  "status": "completed",
  "notes": "Delicious and filling!"
}
```

---

### 12. Track Daily Progress
**Endpoint:** `GET /api/tasks/progress/?date=2024-01-01`

**Description:** Get progress for a specific date. If no date provided, returns today's progress.

**Response:**
```json
[
  {
    "id": "uuid",
    "user": 1,
    "date": "2024-01-01",
    "workout_plan": "uuid",
    "diet_plan": "uuid",
    "exercises_completed": 3,
    "meals_completed": 4,
    "notes": "Great day! Completed all exercises and meals."
  }
]
```

---

### 13. Create Daily Progress
**Endpoint:** `POST /api/tasks/progress/`

**Description:** Log daily progress.

**Request Body:**
```json
{
  "date": "2024-01-01",
  "workout_plan": "workout_plan_uuid",
  "diet_plan": "diet_plan_uuid",
  "exercises_completed": 3,
  "meals_completed": 4,
  "notes": "Feeling strong today!"
}
```

---

## Automatic Integration with AI Chat

### How It Works

1. **User chats with AI** → Provides fitness information
2. **AI generates plans** → Returns workout and diet data
3. **System automatically saves** → Creates WorkoutPlan and DietPlan
4. **Response includes IDs** → `workout_plan_id` and `diet_plan_id`
5. **User can track progress** → Use task management endpoints

### Example AI Chat Response (Enhanced)

```json
{
  "session_id": "chat-session-uuid",
  "message": "Here's your personalized plan!",
  "workout": [...],
  "diet": [...],
  "summary": "Male, 23 years old, 80kg...",
  "workout_plan_id": "workout-plan-uuid",
  "diet_plan_id": "diet-plan-uuid"
}
```

### Accessing Your Plans

After receiving the AI response:

```bash
# Get workout plan details
GET /api/tasks/workout-plans/{workout_plan_id}/

# Get diet plan details
GET /api/tasks/diet-plans/{diet_plan_id}/

# Or view dashboard
GET /api/tasks/dashboard/
```

---

## Database Models

### WorkoutPlan
- `id` (UUID)
- `user` (ForeignKey)
- `chat_session` (ForeignKey) - Links to AI chat
- `name` (String)
- `summary` (Text)
- `status` (active/completed/paused)
- `progress_percentage` (Calculated property)

### Exercise
- `id` (UUID)
- `workout_plan` (ForeignKey)
- `name` (String)
- `sets` (Integer)
- `reps` (String)
- `completed_sets` (Integer)
- `status` (pending/in_progress/completed/skipped)
- `order` (Integer)

### DietPlan
- `id` (UUID)
- `user` (ForeignKey)
- `chat_session` (ForeignKey) - Links to AI chat
- `name` (String)
- `summary` (Text)
- `status` (active/completed/paused)
- `total_daily_calories` (Calculated property)

### Meal
- `id` (UUID)
- `diet_plan` (ForeignKey)
- `meal_type` (breakfast/lunch/snack/dinner)
- `title` (String)
- `items` (JSON array)
- `calories`, `protein`, `carbs`, `fats` (Integers)
- `status` (pending/completed/skipped)

---

## Usage Flow

### Complete User Journey

1. **Chat with AI**
   ```bash
   POST /api/ai/chat/
   ```

2. **AI Creates Plans Automatically**
   - Workout plan saved
   - Diet plan saved
   - IDs returned in response

3. **View Dashboard**
   ```bash
   GET /api/tasks/dashboard/
   ```

4. **Track Exercise Progress**
   ```bash
   PATCH /api/tasks/exercises/{id}/
   {"completed_sets": 3, "status": "completed"}
   ```

5. **Mark Meals Complete**
   ```bash
   PATCH /api/tasks/meals/{id}/
   {"status": "completed"}
   ```

6. **View Progress**
   - Check workout plan progress percentage
   - View completed exercises
   - Monitor daily calorie intake

---

## Testing Examples

### Using cURL

```bash
# Get dashboard
curl -X GET http://localhost:8000/api/tasks/dashboard/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update exercise
curl -X PATCH http://localhost:8000/api/tasks/exercises/EXERCISE_ID/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completed_sets": 3, "status": "completed"}'

# Mark meal complete
curl -X PATCH http://localhost:8000/api/tasks/meals/MEAL_ID/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### Using Python

```python
import requests

headers = {"Authorization": f"Bearer {token}"}

# Get dashboard
response = requests.get(
    "http://localhost:8000/api/tasks/dashboard/",
    headers=headers
)
dashboard = response.json()

# Update exercise
requests.patch(
    f"http://localhost:8000/api/tasks/exercises/{exercise_id}/",
    headers=headers,
    json={"completed_sets": 3, "status": "completed"}
)

# Mark meal complete
requests.patch(
    f"http://localhost:8000/api/tasks/meals/{meal_id}/",
    headers=headers,
    json={"status": "completed"}
)
```

---

## Admin Panel

Access the admin panel at `http://localhost:8000/admin/`:

- View all workout plans with inline exercises
- View all diet plans with inline meals
- Search and filter by user, status, date
- Monitor user progress

---

## Summary

The Task Management System seamlessly integrates with the AI Chat to automatically create trackable fitness plans. Users can:

✅ Get AI-generated workout and diet plans
✅ Automatically save plans as trackable tasks
✅ Mark exercises and meals as completed
✅ Track progress with percentages
✅ View daily progress overview
✅ Manage multiple plans
✅ Access everything via REST API

**Happy tracking! 💪📊**
