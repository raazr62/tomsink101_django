import json
import re
import os
from openai import OpenAI
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    ChatMessageSerializer,
    ModifyPlanRequestSerializer
)
from django.conf import settings


def get_openai_client():
    """Initialize OpenAI client with API key from environment."""
    api_key = settings.OPENAI_API_KEY
    print(f"Using OpenAI API Key: {api_key}")  # Debugging line to check if the key is being read
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def save_workout_plan_as_task(user, session, workout_data, summary):
    """Save workout plan as a trackable task."""
    from apps.task.models import WorkoutPlan, Exercise
    
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
    
    # Create exercises
    for index, exercise_data in enumerate(workout_data):
        Exercise.objects.create(
            workout_plan=workout_plan,
            name=exercise_data.get('exercise', 'Unnamed Exercise'),
            sets=exercise_data.get('sets', 3),
            reps=str(exercise_data.get('reps', '10-12')),
            order=index,
            status='pending'
        )
    
    return workout_plan


def save_diet_plan_as_task(user, session, diet_data, summary):
    """Save diet plan as a trackable task."""
    from apps.task.models import DietPlan, Meal
    
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
    
    # Create meals
    for index, meal_data in enumerate(diet_data):
        meal_type = meal_data.get('meal', '').lower()
        nutrients = meal_data.get('nutrients', {})
        
        Meal.objects.create(
            diet_plan=diet_plan,
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

# System prompt for the AI
SYSTEM_PROMPT = """
You are a professional workout coach and AI assistant.
You help users with their workouts, fitness goals, and plans.
You NEVER answer non-fitness questions.

You must ALWAYS respond in **strict JSON** format like this:
{
  "message": "natural detail reply text here",
  "workout": [],
  "diet": [],
  "summary": "",
  "is_modification": false
}

User Profile Summary: {summary}

Current Workout Plan:
{workout}

Current Diet Plan:
{diet}

User Question: {user_input}

Previous Conversation:
{conversation_history}


If you are providing a workout plan, include it in "workout" as a JSON array of objects like:
[
  {{"exercise": "Shoulder Press", "sets": 3, "reps": "10–12"}},
  {{"exercise": "Bicep Curls", "sets": 3, "reps": "10–12"}},
  ...  
]

If you are providing a diet plan, include it in "diet" as a JSON array of objects like:
[
  {{"meal": "Breakfast", "title": "..." , "items": ["...", .....], "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}}},
  {{"meal": "Lunch", "title": "..." , "items": ["...", ....], "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}}},
  {{"meal": "Snack", "title": "..." , "items": ["...", ....], "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}}},
  {{"meal": "Dinner", "title": "..." , "items": ["...", ....], "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}}},

i need only the 4 meal. Breakfast, Lunch, Snack and dinner. In each meal item give alteast 3-4 food or more. 
...
]

If you are providing a diet plan or workout plan, include a summary in "summary" like:
    "summary": "User information"

IMPORTANT RULES:
1. When a user asks for ANY fitness plan (workout, diet), you MUST collect their complete info first.
2. Required information:
   - gender (male/female)
   - age (in years)
   - weight (in kg)
   - height (in feet)
   - experience_level (beginner, intermediate, advanced)
   - health conditions like injury or physical limitation
   - goal (gain muscle, lose weight, stay fit, etc.)
   - preffered timeline to achieve the goal
   - workout place (Home, Gym)
   - dietary issues (optional: allargic etc.)

3. Ask for ONLY ONE missing piece of information at a time and aslo give him the context why need and also add suggestions. Be conversational and friendly.
4. Once you have ALL required information, ALWAYS generate all four together:
   - workout plan
   - diet plan
   - summary

5. NEVER generate only one or two or three - always provide all four components together.
6. In summary, include all the user info you have collected so far.
7. If user ask any basic question then you can give ans, doesn't need to get complete info.

8. **WORKOUT/DIET MODIFICATION REQUESTS**: When a user asks to modify their existing workout or diet plan (e.g., "Add more cardio", "Replace plank with another exercise", "Make meals vegetarian", "I don't like chicken"):
   - Look at their current workout and diet plans provided above
   - Provide the COMPLETE updated workout AND diet plan with the requested changes
   - Set "is_modification": true in the response
   - Keep exercises/meals they didn't mention changing
   - Make only the changes they requested
   - Provide the full plan so it can replace the old one
   - Consider the user's profile summary when making modifications

9. For basic questions about exercises (like "What is Plank?", "How to do Push-ups?"), provide helpful explanation in "message" field and keep "workout" and "diet" as empty arrays.

if user ask only for diet plan or only for workout plan, include all "diet" and "workout". Because all are related to each other.
Never include extra text outside JSON.
Never include markdown or explanations.
Just return pure JSON.
"""


class ChatView(APIView):
    """
    API View for handling chat interactions with AI.
    
    POST: Send a message and get AI response
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_input = serializer.validated_data['user_input']
        session_id = serializer.validated_data.get('session_id')

        # Get or create chat session
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(user=request.user)

        # Get user's active workout and diet plans for context (from specific_chat.py functionality)
        from apps.task.models import WorkoutPlan, DietPlan
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
        
        # Build workout context
        workout_context = []
        if active_workout:
            for exercise in active_workout.exercises.all().order_by('order'):
                workout_context.append({
                    "exercise": exercise.name,
                    "sets": exercise.sets,
                    "reps": exercise.reps
                })
        
        # Build diet context
        diet_context = []
        if active_diet:
            for meal in active_diet.meals.all().order_by('order'):
                diet_context.append({
                    "meal": meal.meal_type,
                    "title": meal.title,
                    "items": meal.items,
                    "nutrients": {
                        "calories": meal.calories,
                        "protein": meal.protein,
                        "carbs": meal.carbs,
                        "fats": meal.fats
                    }
                })
        
        # Get summary from last message or active plan
        summary_context = ""
        last_message = session.messages.filter(summary__isnull=False).last()
        if last_message and last_message.summary:
            summary_context = last_message.summary
        elif active_workout and active_workout.summary:
            summary_context = active_workout.summary
        elif active_diet and active_diet.summary:
            summary_context = active_diet.summary

        # Build conversation context from previous messages
        conversation_text = ""
        previous_messages = session.messages.all()
        for msg in previous_messages:
            conversation_text += f"User: {msg.user_message}\nAI: {msg.ai_message}\n"
        
        if not conversation_text:
            conversation_text = "No previous conversation"

        try:
            # Initialize OpenAI client
            client = get_openai_client()
            
            # Call OpenAI API with context (similar to specific_chat.py)
            # Use string replacement instead of .format() to avoid issues with JSON braces
            system_prompt_formatted = SYSTEM_PROMPT.replace('{summary}', summary_context)
            system_prompt_formatted = system_prompt_formatted.replace('{workout}', json.dumps(workout_context, indent=2) if workout_context else "No active workout plan")
            system_prompt_formatted = system_prompt_formatted.replace('{diet}', json.dumps(diet_context, indent=2) if diet_context else "No active diet plan")
            system_prompt_formatted = system_prompt_formatted.replace('{user_input}', user_input)
            system_prompt_formatted = system_prompt_formatted.replace('{conversation_history}', conversation_text)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt_formatted},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
            )

            ai_reply = response.choices[0].message.content.strip()

            # Clean markdown code blocks if present
            ai_reply = re.sub(r'^```json\s*', '', ai_reply)
            ai_reply = re.sub(r'^```\s*', '', ai_reply)
            ai_reply = re.sub(r'\s*```$', '', ai_reply)
            ai_reply = ai_reply.strip()

            # Parse JSON response
            response_json = json.loads(ai_reply)
            ai_message = response_json.get("message", "")
            diet = response_json.get("diet", [])
            workout = response_json.get("workout", [])
            summary = response_json.get("summary", "")
            is_modification = response_json.get("is_modification", False)

            # Save message to database
            chat_message = ChatMessage.objects.create(
                session=session,
                user_message=user_input,
                ai_message=ai_message,
                workout=workout if workout else None,
                diet=diet if diet else None,
                summary=summary if summary else None
            )

            # Save workout and diet plans as trackable tasks
            # NEW: Handle modifications by pausing old plans (from specific_chat.py)
            workout_plan_id = None
            diet_plan_id = None
            
            if workout and len(workout) > 0:
                # If this is a modification, pause the old workout plan
                if is_modification and active_workout:
                    active_workout.status = 'paused'
                    active_workout.save()
                
                workout_plan = save_workout_plan_as_task(request.user, session, workout, summary)
                if workout_plan:
                    workout_plan_id = str(workout_plan.id)
            
            if diet and len(diet) > 0:
                # If this is a modification, pause the old diet plan
                if is_modification and active_diet:
                    active_diet.status = 'paused'
                    active_diet.save()
                
                diet_plan = save_diet_plan_as_task(request.user, session, diet, summary)
                if diet_plan:
                    diet_plan_id = str(diet_plan.id)

            # Prepare response
            response_data = {
                'session_id': str(session.id),
                'message': ai_message,
                'workout': workout,
                'diet': diet,
                'summary': summary,
                'is_modification': is_modification,
                'workout_plan_id': workout_plan_id,
                'diet_plan_id': diet_plan_id
            }

            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "AI response generated successfully",
                "data":response_data} , status=status.HTTP_200_OK)

        except json.JSONDecodeError as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "Failed to parse AI response", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "An error occurred", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatSessionListView(APIView):
    """
    API View for listing all chat sessions for the authenticated user.
    
    GET: List all sessions
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Chat sessions retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ChatSessionDetailView(APIView):
    """
    API View for retrieving a specific chat session with all messages.
    
    GET: Retrieve session details
    DELETE: Delete a session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        serializer = ChatSessionDetailSerializer(session)
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Chat session retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def delete(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.delete()
        return Response({
            "status": status.HTTP_204_NO_CONTENT,
            "success": True,
            "message": "Chat session deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT
            )


class ChatSessionCreateView(APIView):
    """
    API View for creating a new chat session.
    
    POST: Create new session
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = ChatSession.objects.create(user=request.user)
        serializer = ChatSessionSerializer(session)
        return Response({
            "status": status.HTTP_201_CREATED,
            "success": True,
            "message": "Chat session created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ChatSessionPlansView(APIView):
    """
    API View for getting all workout and diet plans associated with a chat session.
    
    GET: List all plans (workout and diet) for a specific session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        from apps.task.models import WorkoutPlan, DietPlan
        from apps.task.serializers import WorkoutPlanSerializer, DietPlanSerializer
        
        # Get all workout plans for this session
        workout_plans = WorkoutPlan.objects.filter(
            chat_session=session,
            user=request.user
        ).order_by('-created_at')
        
        # Get all diet plans for this session
        diet_plans = DietPlan.objects.filter(
            chat_session=session,
            user=request.user
        ).order_by('-created_at')
        
        workout_serializer = WorkoutPlanSerializer(workout_plans, many=True)
        diet_serializer = DietPlanSerializer(diet_plans, many=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Session plans retrieved successfully",
            "data": {
                "session_id": str(session.id),
                "workout_plans": workout_serializer.data,
                "diet_plans": diet_serializer.data,
                "workout_plans_count": workout_plans.count(),
                "diet_plans_count": diet_plans.count()
            }
        }, status=status.HTTP_200_OK)


class ModifyPlanView(APIView):
    """
    API View for modifying existing workout and diet plans.
    
    POST: Send modification request to modify workout/diet plans
    
    This endpoint allows users to request modifications to their existing plans
    by providing natural language requests like:
    - "Add more cardio exercises"
    - "Replace chicken with fish"
    - "Make the workout easier"
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ModifyPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        modification_request = serializer.validated_data['modification_request']
        session_id = serializer.validated_data.get('session_id')
        workout_plan_id = serializer.validated_data.get('workout_plan_id')
        diet_plan_id = serializer.validated_data.get('diet_plan_id')

        # Get or create chat session
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(user=request.user)

        # Get the specific plans to modify
        from apps.task.models import WorkoutPlan, DietPlan
        
        workout_plan = None
        diet_plan = None
        
        if workout_plan_id:
            workout_plan = get_object_or_404(WorkoutPlan, id=workout_plan_id, user=request.user)
        
        if diet_plan_id:
            diet_plan = get_object_or_404(DietPlan, id=diet_plan_id, user=request.user)

        # Build workout context from the specified plan
        workout_context = []
        if workout_plan:
            for exercise in workout_plan.exercises.all().order_by('order'):
                workout_context.append({
                    "exercise": exercise.name,
                    "sets": exercise.sets,
                    "reps": exercise.reps
                })
        
        # Build diet context from the specified plan
        diet_context = []
        if diet_plan:
            for meal in diet_plan.meals.all().order_by('order'):
                diet_context.append({
                    "meal": meal.meal_type,
                    "title": meal.title,
                    "items": meal.items,
                    "nutrients": {
                        "calories": meal.calories,
                        "protein": meal.protein,
                        "carbs": meal.carbs,
                        "fats": meal.fats
                    }
                })
        
        # Get summary from the plan
        summary_context = ""
        if workout_plan and workout_plan.summary:
            summary_context = workout_plan.summary
        elif diet_plan and diet_plan.summary:
            summary_context = diet_plan.summary

        # Build conversation context from previous messages in session
        conversation_text = ""
        previous_messages = session.messages.all()
        for msg in previous_messages:
            conversation_text += f"User: {msg.user_message}\nAI: {msg.ai_message}\n"
        
        if not conversation_text:
            conversation_text = "No previous conversation"

        # Create a modification-specific system prompt
        modification_prompt = f"""
You are a professional workout coach and AI assistant.
The user wants to MODIFY their existing workout or diet plan.

You must ALWAYS respond in **strict JSON** format like this:
{{
  "message": "natural detail reply text here explaining the modifications",
  "workout": [],
  "diet": [],
  "summary": "",
  "is_modification": true
}}

User Profile Summary: {summary_context}

CURRENT Workout Plan to Modify:
{json.dumps(workout_context, indent=2) if workout_context else "No workout plan to modify"}

CURRENT Diet Plan to Modify:
{json.dumps(diet_context, indent=2) if diet_context else "No diet plan to modify"}

User's Modification Request: {modification_request}

Previous Conversation:
{conversation_text}

IMPORTANT INSTRUCTIONS:
1. The user is requesting a MODIFICATION to their existing plan
2. You MUST provide the COMPLETE updated plan with the requested changes
3. Keep all exercises/meals they didn't ask to change
4. Make ONLY the specific changes they requested
5. Set "is_modification": true in your response
6. If modifying workout, provide complete "workout" array
7. If modifying diet, provide complete "diet" array
8. Maintain the same format as the original plan
9. In "message", explain what changes you made and why

Workout format: [{{"exercise": "name", "sets": 3, "reps": "10-12"}}]
Diet format: [{{"meal": "Breakfast/Lunch/Snack/Dinner", "title": "...", "items": [...], "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}}}]

Never include extra text outside JSON.
Never include markdown or explanations.
Just return pure JSON.
"""

        try:
            # Initialize OpenAI client
            client = get_openai_client()
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": modification_prompt},
                    {"role": "user", "content": modification_request}
                ],
                temperature=0.7,
            )

            ai_reply = response.choices[0].message.content.strip()

            # Clean markdown code blocks if present
            ai_reply = re.sub(r'^```json\s*', '', ai_reply)
            ai_reply = re.sub(r'^```\s*', '', ai_reply)
            ai_reply = re.sub(r'\s*```$', '', ai_reply)
            ai_reply = ai_reply.strip()

            # Parse JSON response
            response_json = json.loads(ai_reply)
            ai_message = response_json.get("message", "")
            new_diet = response_json.get("diet", [])
            new_workout = response_json.get("workout", [])
            new_summary = response_json.get("summary", summary_context)
            is_modification = response_json.get("is_modification", True)

            # Save message to database
            chat_message = ChatMessage.objects.create(
                session=session,
                user_message=modification_request,
                ai_message=ai_message,
                workout=new_workout if new_workout else None,
                diet=new_diet if new_diet else None,
                summary=new_summary if new_summary else None
            )

            # Pause old plans and create new modified plans
            new_workout_plan_id = None
            new_diet_plan_id = None
            
            if new_workout and len(new_workout) > 0:
                # Pause the old workout plan
                if workout_plan:
                    workout_plan.status = 'paused'
                    workout_plan.save()
                
                # Create new modified workout plan
                new_workout_plan = save_workout_plan_as_task(
                    request.user, 
                    session, 
                    new_workout, 
                    new_summary
                )
                if new_workout_plan:
                    new_workout_plan_id = str(new_workout_plan.id)
            
            if new_diet and len(new_diet) > 0:
                # Pause the old diet plan
                if diet_plan:
                    diet_plan.status = 'paused'
                    diet_plan.save()
                
                # Create new modified diet plan
                new_diet_plan = save_diet_plan_as_task(
                    request.user, 
                    session, 
                    new_diet, 
                    new_summary
                )
                if new_diet_plan:
                    new_diet_plan_id = str(new_diet_plan.id)

            # Prepare response
            response_data = {
                'session_id': str(session.id),
                'message': ai_message,
                'workout': new_workout,
                'diet': new_diet,
                'summary': new_summary,
                'is_modification': is_modification,
                'old_workout_plan_id': str(workout_plan_id) if workout_plan_id else None,
                'old_diet_plan_id': str(diet_plan_id) if diet_plan_id else None,
                'new_workout_plan_id': new_workout_plan_id,
                'new_diet_plan_id': new_diet_plan_id
            }

            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Plan modified successfully",
                "data": response_data
            }, status=status.HTTP_200_OK)

        except json.JSONDecodeError as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "Failed to parse AI response",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "An error occurred",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)