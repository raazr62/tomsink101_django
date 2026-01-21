from apps.task.models import DietPlan, Exercise, Meal, WorkoutPlan



# Save workout plan as a celery task
def save_workout_plan_as_task(user, session, workout_data, summary):
    if not workout_data:
        return None
    
    # Create workout plan
    workout_plan = WorkoutPlan.objects.create(
        user=user,
        chat_session=session,
        name=f"Workout Plan - {session.created_at.strftime('%Y-%m-%d')}",
        summary=summary or "AI Generated Workout Plan",
        status='active'
    )
    
    # Create exercises grouped by date
    for day_data in workout_data:
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
    
    return workout_plan

# Save diet plan as a celery task
def save_diet_plan_as_task(user, session, diet_data, summary):
    if not diet_data:
        return None
    
    # Create diet plan
    diet_plan = DietPlan.objects.create(
        user=user,
        chat_session=session,
        name=f"Diet Plan - {session.created_at.strftime('%Y-%m-%d')}",
        summary=summary or "AI Generated Diet Plan",
        status='active'
    )
    
    # Map meal types
    meal_type_map = {
        'breakfast': 'breakfast',
        'lunch': 'lunch',
        'snack': 'snack',
        'dinner': 'dinner'
    }
    
    # Create meals grouped by date
    for day_data in diet_data:
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
    
    return diet_plan
