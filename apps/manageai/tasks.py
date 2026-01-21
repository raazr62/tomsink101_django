from datetime import date, timedelta
import json
import re
from celery import shared_task
from apps.manageai.models import ChatSession
from apps.manageai.utils.system_prompt import SYSTEM_PROMPT_FOR_DIET_BACKGROUND, SYSTEM_PROMPT_FOR_WORKOUT_BACKGROUND
from apps.task.models import DietPlan, Exercise, Meal, WorkoutPlan
from apps.utils.openai_utils import get_openai_client

# generate remaining workouts in background task
@shared_task(bind=True, name='manageai.generate_remaining_workouts')
def generate_remaining_workouts(self, session_id, last_summary, workout_plan_id):
    """
    Generate remaining 29 days of workout plans in the background.
    """
    try:
        print(f"[Celery] Generating remaining workouts for workout_plan {workout_plan_id}...")
        
        session = ChatSession.objects.filter(id=session_id).first()
        if not session:
            print(f"Session {session_id} not found")
            return {"success": False, "error": "Session not found"}
        
        workout_plan = WorkoutPlan.objects.filter(id=workout_plan_id).first()
        if not workout_plan:
            print(f"Workout plan {workout_plan_id} not found")
            return {"success": False, "error": "Workout plan not found"}
        
        # Initialize OpenAI client
        client = get_openai_client()
        
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=29)
        
        system_prompt_formatted = SYSTEM_PROMPT_FOR_WORKOUT_BACKGROUND.format(
            current_date=start_date.strftime('%Y-%m-%d'),
            last_date=end_date.strftime('%Y-%m-%d'),
            last_summary=last_summary if last_summary else ""
        )
        
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt_formatted},
                {"role": "user", "content": f"Generate a complete workout plan with one entry for each day from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. That's 29 days total. Each day should have 4+ exercises. Create 29 separate date objects in the array."}
            ],
            temperature=0.8,
        )
        
        ai_reply = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        ai_reply = re.sub(r'^```json\s*', '', ai_reply)
        ai_reply = re.sub(r'^```\s*', '', ai_reply)
        ai_reply = re.sub(r'\s*```$', '', ai_reply)
        ai_reply = ai_reply.strip()
        
        response_json = json.loads(ai_reply)
        workout = response_json.get("workout", [])
        
        if workout:
            # Add exercises to existing workout plan
            for day_data in workout:
                exercise_date = day_data.get('date')
                exercises = day_data.get('exercise', [])
                
                for index, exercise_data in enumerate(exercises):
                    Exercise.objects.create(
                        workout_plan=workout_plan,
                        name=exercise_data.get('name', 'Unnamed Exercise'),
                        date=exercise_date,
                        sets=exercise_data.get('sets', 3),
                        reps=str(exercise_data.get('reps', '10-12')),
                        weight=exercise_data.get('weight', ''),
                        description=exercise_data.get('description', ''),
                        pro_tips=exercise_data.get('pro_tips', []),
                        order=index,
                        status='pending'
                    )
            
            print(f"[Celery] Successfully generated {len(workout)} days of workout plans")
            return {"success": True, "days_generated": len(workout)}
        
        return {"success": False, "error": "No workout data generated"}
        
    except Exception as e:
        print(f"[Celery] Error generating remaining workouts: {e}")
        return {"success": False, "error": str(e)}

# generate remaining diets in background task
@shared_task(bind=True, name='manageai.generate_remaining_diets')
def generate_remaining_diets(self, session_id, last_summary, diet_plan_id):
    """
    Generate remaining 29 days of diet plans in the background.
    """
    try:
        print(f"[Celery] Generating remaining diets for diet_plan {diet_plan_id}...")
        
        session = ChatSession.objects.filter(id=session_id).first()
        if not session:
            print(f"Session {session_id} not found")
            return {"success": False, "error": "Session not found"}
        
        diet_plan = DietPlan.objects.filter(id=diet_plan_id).first()
        if not diet_plan:
            print(f"Diet plan {diet_plan_id} not found")
            return {"success": False, "error": "Diet plan not found"}
        
        # Initialize OpenAI client
        client = get_openai_client()
        
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=29)
        
        system_prompt_formatted = SYSTEM_PROMPT_FOR_DIET_BACKGROUND.format(
            current_date=start_date.strftime('%Y-%m-%d'),
            last_date=end_date.strftime('%Y-%m-%d'),
            last_summary=last_summary if last_summary else ""
        )
        
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt_formatted},
                {"role": "user", "content": f"Generate a complete diet plan with one entry for each day from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. That's 29 days total. Each day should have 4 meals (Breakfast, Lunch, Snack, Dinner). Create 29 separate date objects in the array."}
            ],
            temperature=0.8,
        )
        
        ai_reply = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        ai_reply = re.sub(r'^```json\s*', '', ai_reply)
        ai_reply = re.sub(r'^```\s*', '', ai_reply)
        ai_reply = re.sub(r'\s*```$', '', ai_reply)
        ai_reply = ai_reply.strip()
        
        response_json = json.loads(ai_reply)
        diet = response_json.get("diet", [])
        
        # Map meal types
        meal_type_map = {
            'breakfast': 'breakfast',
            'lunch': 'lunch',
            'snack': 'snack',
            'dinner': 'dinner'
        }
        
        if diet:
            # Add meals to existing diet plan
            for day_data in diet:
                meal_date = day_data.get('date')
                foods = day_data.get('foods', [])
                
                for index, meal_data in enumerate(foods):
                    meal_type = meal_data.get('meal', '').lower()
                    nutrients = meal_data.get('nutrients', {})
                    
                    Meal.objects.create(
                        diet_plan=diet_plan,
                        date=meal_date,
                        meal_type=meal_type_map.get(meal_type, 'snack'),
                        title=meal_data.get('title', f"{meal_type.capitalize()} Meal"),
                        items=meal_data.get('items', []),
                        calories=nutrients.get('calories', 0),
                        protein=nutrients.get('protein', 0),
                        carbs=nutrients.get('carbs', 0),
                        fats=nutrients.get('fats', 0),
                        order=index,
                        status='pending'
                    )
            
            print(f"[Celery] Successfully generated {len(diet)} days of diet plans")
            return {"success": True, "days_generated": len(diet)}
        
        return {"success": False, "error": "No diet data generated"}
        
    except Exception as e:
        print(f"[Celery] Error generating remaining diets: {e}")
        return {"success": False, "error": str(e)}
