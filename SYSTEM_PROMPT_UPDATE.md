# System Prompt Update - Django AI Plan

## Changes Made

Updated the `SYSTEM_PROMPT` in [apps/ai_plan/views.py](apps/ai_plan/views.py) to ensure the AI returns responses in the exact same format as your FastAPI version.

---

## Fixed Issues

### 1. **Workout Structure**
**Before (Django was returning):**
```json
{
  "workout": [
    {
      "exercise": "Push-ups",  // ❌ Wrong field name
      "sets": 3,
      "reps": "10",
      "description": "...",
      "tips": [...]  // ❌ Wrong field name
      // ❌ Missing: date, weight, pro_tips
    }
  ]
}
```

**After (Now returns):**
```json
{
  "workout": [
    {
      "date": "2026-01-15",  // ✅ Added
      "exercise": [
        {
          "name": "Push-ups",  // ✅ Correct field name
          "sets": 3,
          "reps": "10-12",
          "weight": "",  // ✅ Added (empty for bodyweight)
          "description": "...",
          "pro_tips": [  // ✅ Correct field name
            "Tip 1",
            "Tip 2"
          ]
        }
      ]
    }
  ]
}
```

### 2. **Diet Structure**
**Before (Django was returning):**
```json
{
  "diet": [
    {
      "meal": "Breakfast",
      "foods": ["Oatmeal", "Eggs"]  // ❌ Wrong structure
      // ❌ Missing: date, title, items array, nutrients
    }
  ]
}
```

**After (Now returns):**
```json
{
  "diet": [
    {
      "date": "2026-01-15",  // ✅ Added
      "foods": [
        {
          "meal": "Breakfast",
          "title": "High-protein start",  // ✅ Added
          "items": [  // ✅ Correct structure
            "Whole eggs + egg whites omelet",
            "Oats cooked with milk",
            "Banana"
          ],
          "nutrients": {  // ✅ Added
            "calories": 620,
            "protein": 45,
            "carbs": 70,
            "fats": 18
          }
        }
      ]
    }
  ]
}
```

---

## Key Improvements

### Workout Response
✅ **`date` field** - Added at workout day level (YYYY-MM-DD format)  
✅ **`name` field** - Changed from "exercise" to "name" for exercise name  
✅ **`weight` field** - Now required (e.g., "60-90 kg" or "" for bodyweight)  
✅ **`pro_tips` field** - Changed from "tips" to "pro_tips"  
✅ **Nested structure** - `exercise` is now an array within each workout day  

### Diet Response
✅ **`date` field** - Added at diet day level (YYYY-MM-DD format)  
✅ **`title` field** - Added descriptive meal title  
✅ **`items` array** - Changed from flat "foods" to structured "items" array  
✅ **`nutrients` object** - Added with calories, protein, carbs, fats (all integers)  
✅ **Nested structure** - `foods` array contains meal objects with full details  

### General Improvements
✅ **Explicit examples** - Added complete example responses in the prompt  
✅ **Field name enforcement** - Emphasized correct field names (name vs exercise, pro_tips vs tips)  
✅ **Required fields** - Clearly marked all fields as REQUIRED  
✅ **Format specifications** - Detailed format for each field type  

---

## Response Format Now Matches FastAPI

The Django API will now return responses in the **exact same format** as your FastAPI version:

```json
{
  "status": 200,
  "success": true,
  "message": "Chat processed successfully",
  "data": {
    "session_id": "uuid",
    "response": {
      "message": "AI's natural language response",
      "workout": [
        {
          "date": "2026-01-15",
          "exercise": [
            {
              "name": "Exercise Name",
              "sets": 4,
              "reps": "10-12",
              "weight": "60-90 kg",
              "description": "Full description...",
              "pro_tips": ["Tip 1", "Tip 2"]
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
              "items": ["Item 1", "Item 2", "Item 3"],
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
      "summary": "Complete user profile summary"
    }
  }
}
```

---

## Testing the Changes

### 1. Restart the Server
```bash
python manage.py runserver 0.0.0.0:8007
```

### 2. Test with Workout Request
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Create a beginner workout plan for fat loss",
    "summary": "Male, 20 years old, 100 kg, height 4 feet 5 inches, fat-loss goal"
  }'
```

**Expected Response Structure:**
- ✅ `workout[0].date` should be present
- ✅ `workout[0].exercise` should be an array
- ✅ Each exercise should have `name`, `sets`, `reps`, `weight`, `description`, `pro_tips`
- ✅ `weight` field should be present (even if empty string for bodyweight)
- ✅ `pro_tips` should be an array with at least 2 tips

### 3. Test with Diet Request
```bash
curl -X POST http://localhost:8007/api/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Give me a diet plan for fat loss",
    "summary": "Male, 20 years old, 100 kg, fat-loss goal, no dietary restrictions"
  }'
```

**Expected Response Structure:**
- ✅ `diet[0].date` should be present
- ✅ `diet[0].foods` should be an array of meal objects
- ✅ Each meal should have `meal`, `title`, `items`, `nutrients`
- ✅ `items` should be an array of food items (not a flat array)
- ✅ `nutrients` should have `calories`, `protein`, `carbs`, `fats` (all integers)

---

## What Changed in the Code

**File**: [apps/ai_plan/views.py](apps/ai_plan/views.py)

**Location**: Lines ~17-200 (SYSTEM_PROMPT constant)

**Changes**:
1. Expanded the system prompt from ~70 lines to ~190 lines
2. Added explicit field name requirements
3. Added two complete example responses
4. Added "CRITICAL RULES" sections for both workout and diet
5. Emphasized required fields and proper data types
6. Added date field requirements (using today's date: 2026-01-15)
7. Clarified nested structure expectations

---

## Troubleshooting

### If AI Still Returns Wrong Format

1. **Check OpenAI API Response**:
   - The Django view logs raw AI responses
   - Check console output for `print("AI Reply:", ai_reply)`
   
2. **Verify JSON Parsing**:
   - The code catches `json.JSONDecodeError`
   - Error will be returned with raw response

3. **Temperature Setting**:
   - Currently set to 0.7
   - For more consistent formatting, consider lowering to 0.3-0.5

4. **Model Consistency**:
   - Using `gpt-4o-mini`
   - If responses are inconsistent, try `gpt-4` for better instruction following

---

## Next Steps

1. ✅ **System prompt updated** - Now matches FastAPI format
2. ⏳ **Test with real requests** - Verify AI returns correct structure
3. ⏳ **Monitor responses** - Check if all required fields are present
4. ⏳ **Fine-tune if needed** - Adjust temperature or model if necessary

---

## Status

✅ **Implementation Complete**  
✅ **No Syntax Errors**  
✅ **Django Check Passed**  
⏳ **Ready for Testing**

The Django AI Plan API should now return responses in the exact same format as your FastAPI version, with all the required fields including:
- `date` at workout/diet day level
- `weight` in exercises
- `pro_tips` (not "tips")
- `title` in diet meals
- `items` array for food items
- `nutrients` object with all nutritional values
