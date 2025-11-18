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
    ChatMessageSerializer
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
  "summary": ""
}


If you are providing a workout plan, include it in "workout" as a JSON array of objects like:
[
  {"exercise": "Shoulder Press", "sets": 3, "reps": "10–12"},
  {"exercise": "Bicep Curls", "sets": 3, "reps": "10–12"},
  ...  
]

If you are providing a diet plan, include it in "diet" as a JSON array of objects like:
[
  {"meal": "Breakfast", "title": "..." , "items": ["...", .....], "nutrients": {"calories": 400, "protein": 30, "carbs": 50, "fats": 10}},
  {"meal": "Lunch", "title": "..." , "items": ["...", ....], "nutrients": {"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}},
  {"meal": "Snack", "title": "..." , "items": ["...", ....], "nutrients": {"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}},
  {"meal": "Dinner", "title": "..." , "items": ["...", ....], "nutrients": {"calories": 400, "protein": 30, "carbs": 50, "fats": 10}},

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

        # Build conversation context from previous messages
        conversation_text = ""
        previous_messages = session.messages.all()
        for msg in previous_messages:
            conversation_text += f"User: {msg.user_message}\nAI: {msg.ai_message}\n"
        conversation_text += f"User: {user_input}\nAI:"

        try:
            # Initialize OpenAI client
            client = get_openai_client()
            
            # Call OpenAI API
            response = client.responses.create(
                model="gpt-4o",
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": conversation_text}
                ],
                temperature=0.8,
            )

            ai_reply = response.output[0].content[0].text.strip()

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
            workout_plan_id = None
            diet_plan_id = None
            
            if workout and len(workout) > 0:
                workout_plan = save_workout_plan_as_task(request.user, session, workout, summary)
                if workout_plan:
                    workout_plan_id = str(workout_plan.id)
            
            if diet and len(diet) > 0:
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
        serializer = ChatSessionSerializer(session)
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