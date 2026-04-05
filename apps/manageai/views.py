import json
import re
from datetime import date
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.manageai.utils.system_prompt import SYSTEM_PROMPT
from apps.task.models import DietPlan, WorkoutPlan, Exercise
from apps.utils.openai_utils import get_openai_client
from apps.manageai.tasks import generate_remaining_workouts, generate_remaining_diets
from apps.manageai.utils.plan_save import save_diet_plan_as_task, save_workout_plan_as_task

from .models import ChatSession, ChatMessage

from .serializers import (
    ChatRequestSerializer,
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    ModifyPlanRequestSerializer
)



# Chat Session & Message 
class ChatView(APIView):
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
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
        
        # Build workout context
        workout_context = []
        if active_workout:
            for exercise in active_workout.exercises.all().order_by('order'):
                workout_context.append({
                    "name": exercise.name,
                    "sets": exercise.sets,
                    "reps": exercise.reps,
                    "weight": exercise.weight,
                    "description": exercise.description or "",
                    "pro_tips": exercise.pro_tips or []
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

        # Build conversation context from previous messages (chat messages only)
        conversation_text = ""
        previous_messages = session.messages.filter(message_type='chat')
        for msg in previous_messages:
            conversation_text += f"User: {msg.user_message}\nAI: {msg.ai_message}\n"
        
        if not conversation_text:
            conversation_text = "No previous conversation"

        try:
            # Initialize OpenAI client
            client = get_openai_client()
            
            # Call OpenAI API with context
            system_prompt_formatted = SYSTEM_PROMPT.format(
                current_date=date.today().strftime('%Y-%m-%d'),
                last_summary=summary_context if summary_context else "",
                conversation_history=conversation_text
            )
            
            response = client.chat.completions.create(
                model="gpt-5.2",
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

            # Save message to database
            chat_message = ChatMessage.objects.create(
                session=session,
                user_message=user_input,
                ai_message=ai_message,
                workout=workout if workout else None,
                diet=diet if diet else None,
                summary=summary if summary else None,
                message_type='chat'
            )

            # Save workout and diet plans as trackable tasks
            workout_plan_id = None
            diet_plan_id = None
            
            if workout and len(workout) > 0:
                # Pause old active workout plan
                if active_workout:
                    active_workout.status = 'paused'
                    active_workout.save()
                
                workout_plan = save_workout_plan_as_task(request.user, session, workout, summary)
                if workout_plan:
                    workout_plan_id = str(workout_plan.id)
                    
                    # Start Celery background task to generate remaining 29 days
                    generate_remaining_workouts.delay(
                        str(session.id), summary, workout_plan_id
                    )
            
            if diet and len(diet) > 0:
                # Pause old active diet plan
                if active_diet:
                    active_diet.status = 'paused'
                    active_diet.save()
                
                diet_plan = save_diet_plan_as_task(request.user, session, diet, summary)
                if diet_plan:
                    diet_plan_id = str(diet_plan.id)
                    
                    # Start Celery background task to generate remaining 29 days
                    generate_remaining_diets.delay(
                        str(session.id), summary, diet_plan_id
                    )

            # Prepare response
            response_data = {
                'session_id': str(session.id),
                'message': ai_message,
                'workout': workout,
                'diet': diet,
                'summary': summary,
                'workout_plan_id': workout_plan_id,
                'diet_plan_id': diet_plan_id,
                'plane_generated': True if workout_plan_id or diet_plan_id else False
            }

            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "AI response generated successfully",
                "data":response_data
            } , status=status.HTTP_200_OK)

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


class LastChatSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the most recent session for the user
        session = ChatSession.objects.filter(user=request.user).order_by('-updated_at').first()
        
        if not session:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "success": False,
                "message": "No chat sessions found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ChatSessionDetailSerializer(session)
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Last chat session retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


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

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ModifyPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        modification_request = serializer.validated_data['modification_request']
        session_id = serializer.validated_data.get('session_id')
        workout_plan_id = serializer.validated_data.get('workout_plan_id')
        diet_plan_id = serializer.validated_data.get('diet_plan_id')
        exercise_id = serializer.validated_data.get('exercise_id')
        meal_id = serializer.validated_data.get('meal_id')

        # Get or create chat session
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(user=request.user)


        # CASE 1: Update specific exercise in place**
        if exercise_id:
            return self._update_specific_exercise(
                request, session, exercise_id, modification_request
            )

        # CASE 2: Update specific meal in place**
        if meal_id:
            return self._update_specific_meal(
                request, session, meal_id, modification_request
            )

        # CASE 3: Update entire plan (original behavior - creates new plan)**
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
                    "name": exercise.name,
                    "sets": exercise.sets,
                    "reps": exercise.reps,
                    "weight": exercise.weight,
                    "description": exercise.description or "",
                    "pro_tips": exercise.pro_tips or []
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

        # Build conversation context from previous messages in session (modification messages only)
        conversation_text = ""
        previous_messages = session.messages.filter(message_type='modification')
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
  "summary": ""
}}

User Profile Summary: {summary_context}

CURRENT Workout Plan to Modify:
{json.dumps(workout_context, indent=2) if workout_context else "No workout plan to modify"}

CURRENT Diet Plan to Modify:
{json.dumps(diet_context, indent=2) if diet_context else "No diet plan to modify"}

User's Modification Request: {modification_request}

Previous Conversation:
{conversation_text}

Current date is {date.today().strftime('%Y-%m-%d')}.

IMPORTANT INSTRUCTIONS:
1. The user is requesting a MODIFICATION to their existing plan
2. You MUST provide the COMPLETE updated plan with the requested changes
3. Keep all exercises/meals they didn't ask to change
4. Make ONLY the specific changes they requested
5. If modifying workout, provide complete "workout" array
6. If modifying diet, provide complete "diet" array
7. Maintain the same format as the original plan
8. In "message", explain what changes you made and why
9. Generate plans for a single day only

Workout format (with date):
[
  {{
    "date": "{date.today().strftime('%Y-%m-%d')}",
    "exercise": [
        {{
            "name": "Exercise Name",
            "sets": 3,
            "reps": "10-12",
            "weight": "10-15 kg" or "",
            "description": "Detailed explanation including: what the exercise is, how to perform it step-by-step, correct form and common mistakes to avoid.",
            "pro_tips": ["tip1", "tip2", "tip3"]
        }}
    ]
  }}
]

Diet format (with date):
[
  {{
    "date": "{date.today().strftime('%Y-%m-%d')}",
    "foods": [
        {{
            "meal": "Breakfast/Lunch/Snack/Dinner",
            "title": "...",
            "items": [...],
            "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}
        }}
    ]
  }}
]

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

            # Save message to database
            chat_message = ChatMessage.objects.create(
                session=session,
                user_message=modification_request,
                ai_message=ai_message,
                workout=new_workout if new_workout else None,
                diet=new_diet if new_diet else None,
                summary=new_summary if new_summary else None,
                message_type='modification'
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
                    
                    # Start Celery background task to generate remaining 29 days
                    generate_remaining_workouts.delay(
                        str(session.id), new_summary, new_workout_plan_id
                    )
            
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
                    
                    # Start Celery background task to generate remaining 29 days
                    generate_remaining_diets.delay(
                        str(session.id), new_summary, new_diet_plan_id
                    )

            # Prepare response
            response_data = {
                'session_id': str(session.id),
                'message': ai_message,
                'workout': new_workout,
                'diet': new_diet,
                'summary': new_summary,
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
    
    # update the specific exercise
    def _update_specific_exercise(self, request, session, exercise_id, modification_request):
        
        try:
            # Get the specific exercise
            exercise = Exercise.objects.select_related('workout_plan').get(id=exercise_id)
            
            # Verify the user owns this exercise's workout plan
            if exercise.workout_plan.user != request.user:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "success": False,
                    "error": "You don't have permission to modify this exercise",
                    "details": "Exercise doesn't belong to your workout plan"
                }, status=status.HTTP_403_FORBIDDEN)
            
            workout_plan = exercise.workout_plan
            
            # Build context for just this exercise
            exercise_context = {
                "name": exercise.name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight": exercise.weight,
                "description": exercise.description or "",
                "pro_tips": exercise.pro_tips or [],
                "date": str(exercise.date) if exercise.date else "N/A"
            }
            
            # Get workout plan summary
            summary_context = workout_plan.summary or "AI Generated Workout Plan"
            
            # Build conversation context from session (modification messages only)
            conversation_text = ""
            previous_messages = session.messages.filter(message_type='modification')
            for msg in previous_messages:
                conversation_text += f"User: {msg.user_message}\nAI: {msg.ai_message}\n"
            
            if not conversation_text:
                conversation_text = "No previous conversation"
            
            # Create system prompt for single exercise modification
            modification_prompt = f"""
You are a professional workout coach and AI assistant.
The user wants to MODIFY their existing workout EXERCISE.

You must ALWAYS respond in **strict JSON** format like this:
{{
  "message": "natural detail reply text here explaining the modifications",
  "exercise": {{
    "name": "Exercise Name",
    "sets": 3,
    "reps": "10-12",
    "weight": "10-15 kg" or "",
    "description": "Detailed explanation",
    "pro_tips": ["tip1", "tip2"]
  }}
}}

User Profile Summary: {summary_context}

CURRENT Exercise to Modify:
{json.dumps(exercise_context, indent=2)}

User's Modification Request: {modification_request}

Previous Conversation:
{conversation_text}

IMPORTANT INSTRUCTIONS:
1. The user is requesting a MODIFICATION to a SINGLE exercise
2. Return ONLY the modified exercise data
3. Make ONLY the specific changes requested
4. Keep all fields from the original exercise (name, description, etc.)
5. In "message", explain what changes you made and why
6. Be specific and detailed in the exercise description

Never include extra text outside JSON.
Just return pure JSON.
"""
            
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
            modified_exercise = response_json.get("exercise", {})

            # Save message to database
            chat_message = ChatMessage.objects.create(
                session=session,
                user_message=modification_request,
                ai_message=ai_message,
                workout=None,
                diet=None,
                summary=None,
                message_type='modification'
            )

            # Update the exercise in place
            if modified_exercise:
                exercise.name = modified_exercise.get('name', exercise.name)
                exercise.sets = modified_exercise.get('sets', exercise.sets)
                exercise.reps = str(modified_exercise.get('reps', exercise.reps))
                exercise.weight = modified_exercise.get('weight', exercise.weight) or ''
                exercise.description = modified_exercise.get('description', exercise.description)
                exercise.pro_tips = modified_exercise.get('pro_tips', exercise.pro_tips or [])
                exercise.updated_at = date.today()
                exercise.save()

            # Prepare response
            response_data = {
                'session_id': str(session.id),
                'message': ai_message,
                'exercise_id': str(exercise.id),
                'workout_plan_id': str(workout_plan.id),
                'updated_exercise': {
                    'id': str(exercise.id),
                    'name': exercise.name,
                    'sets': exercise.sets,
                    'reps': exercise.reps,
                    'weight': exercise.weight,
                    'description': exercise.description,
                    'pro_tips': exercise.pro_tips,
                    'date': str(exercise.date) if exercise.date else None
                }
            }

            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Exercise updated successfully",
                "data": response_data
            }, status=status.HTTP_200_OK)

        except json.JSONDecodeError as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "Failed to parse AI response",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exercise.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "success": False,
                "error": "Exercise not found",
                "details": f"No exercise with ID {exercise_id} exists"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "An error occurred",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _update_specific_meal(self, request, session, meal_id, modification_request):
        """Update a specific meal in the database without creating a new plan."""
        from apps.task.models import Meal
        
        try:
            # Get the specific meal
            meal = Meal.objects.select_related('diet_plan').get(id=meal_id)
            
            # Verify the user owns this meal's diet plan
            if meal.diet_plan.user != request.user:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "success": False,
                    "error": "You don't have permission to modify this meal",
                    "details": "Meal doesn't belong to your diet plan"
                }, status=status.HTTP_403_FORBIDDEN)
            
            diet_plan = meal.diet_plan
            
            # Build context for just this meal
            meal_context = {
                "meal": meal.meal_type,
                "title": meal.title,
                "items": meal.items,
                "nutrients": {
                    "calories": meal.calories,
                    "protein": meal.protein,
                    "carbs": meal.carbs,
                    "fats": meal.fats
                },
                "date": str(meal.date) if meal.date else "N/A"
            }
            
            # Get diet plan summary
            summary_context = diet_plan.summary or "AI Generated Diet Plan"
            
            # Build conversation context from session (modification messages only)
            conversation_text = ""
            previous_messages = session.messages.filter(message_type='modification')
            for msg in previous_messages:
                conversation_text += f"User: {msg.user_message}\nAI: {msg.ai_message}\n"
            
            if not conversation_text:
                conversation_text = "No previous conversation"
            
            # Create system prompt for single meal modification
            modification_prompt = f"""
You are a professional nutrition coach and AI assistant.
The user wants to MODIFY their existing MEAL.

You must ALWAYS respond in **strict JSON** format like this:
{{
  "message": "natural detail reply text here explaining the modifications",
  "meal": {{
    "title": "Meal Title",
    "items": ["item1", "item2", ...],
    "nutrients": {{"calories": 400, "protein": 30, "carbs": 50, "fats": 10}}
  }}
}}

User Profile Summary: {summary_context}

CURRENT Meal to Modify:
{json.dumps(meal_context, indent=2)}

User's Modification Request: {modification_request}

Previous Conversation:
{conversation_text}

IMPORTANT INSTRUCTIONS:
1. The user is requesting a MODIFICATION to a SINGLE meal
2. Return ONLY the modified meal data
3. Make ONLY the specific changes requested
4. Keep the meal type ({meal.meal_type}) unless user specifies otherwise
5. In "message", explain what changes you made and why
6. Provide realistic nutritional values

Never include extra text outside JSON.
Just return pure JSON.
"""
            
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
            modified_meal = response_json.get("meal", {})

            # Save message to database
            chat_message = ChatMessage.objects.create(
                session=session,
                user_message=modification_request,
                ai_message=ai_message,
                workout=None,
                diet=None,
                summary=None,
                message_type='modification'
            )

            # Update the meal in place
            if modified_meal:
                meal.title = modified_meal.get('title', meal.title)
                meal.items = modified_meal.get('items', meal.items)
                nutrients = modified_meal.get('nutrients', {})
                meal.calories = nutrients.get('calories', meal.calories)
                meal.protein = nutrients.get('protein', meal.protein)
                meal.carbs = nutrients.get('carbs', meal.carbs)
                meal.fats = nutrients.get('fats', meal.fats)
                meal.save()

            # Prepare response
            response_data = {
                'session_id': str(session.id),
                'message': ai_message,
                'meal_id': str(meal.id),
                'diet_plan_id': str(diet_plan.id),
                'updated_meal': {
                    'id': str(meal.id),
                    'meal_type': meal.meal_type,
                    'title': meal.title,
                    'items': meal.items,
                    'nutrients': {
                        'calories': meal.calories,
                        'protein': meal.protein,
                        'carbs': meal.carbs,
                        'fats': meal.fats
                    },
                    'date': str(meal.date) if meal.date else None
                }
            }

            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Meal updated successfully",
                "data": response_data
            }, status=status.HTTP_200_OK)

        except json.JSONDecodeError as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "Failed to parse AI response",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Meal.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "success": False,
                "error": "Meal not found",
                "details": f"No meal with ID {meal_id} exists"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "error": "An error occurred",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)