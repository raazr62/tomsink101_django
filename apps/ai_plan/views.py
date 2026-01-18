import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from apps.utils.openai_utils import get_openai_client
from .models import AIPlanSession, AIPlanConversation
from .serializers import (
    AskRequestSerializer,
    AskResponseSerializer,
    ChatResponseSerializer,
    SessionDetailSerializer,
)


SYSTEM_PROMPT = """
You are a professional workout coach and AI assistant.
You help users with their workouts, fitness goals, and plans.
You NEVER answer non-fitness questions.

You must ALWAYS respond in **strict JSON** format exactly as shown below.

User Profile Summary: {summary}

Current Workout Plan:
{workout}

Current Diet Plan:
{diet}

User Question: {user_input}

Previous Conversation:
{conversation_history}

RESPONSE FORMAT (MANDATORY):
You MUST return a JSON object with these exact fields:
{{
  "message": "your natural language response here",
  "workout": [],
  "diet": [],
  "summary": "updated user profile summary with all gathered information"
}}

IMPORTANT RULES:
1. For basic questions (like "What is Plank?"), provide explanation in "message" field and keep "workout" and "diet" as empty arrays [].
2. For workout requests or modifications, provide the COMPLETE workout plan in "workout" array using the EXACT format below.
3. For diet requests or modifications, provide the COMPLETE diet plan in "diet" array using the EXACT format below.
4. ALWAYS update the "summary" field with ALL user information gathered so far (age, weight, height, goals, restrictions, etc.).
5. Never skip any fields - all fields are REQUIRED.

WORKOUT ARRAY FORMAT (use today's date: 2026-01-15):
[
  {{
    "date": "2026-01-15",
    "exercise": [
      {{
        "name": "Exercise Name",
        "sets": 4,
        "reps": "10-12",
        "weight": "60-90 kg",
        "description": "Detailed description of how to perform the exercise correctly",
        "pro_tips": [
          "First important tip",
          "Second important tip"
        ]
      }}
    ]
  }}
]

CRITICAL WORKOUT RULES:
- "name" field is REQUIRED (not "exercise")
- "weight" field is REQUIRED (use "60-90 kg" format or empty string "" if bodyweight)
- "pro_tips" field is REQUIRED (array with at least 2 tips, not "tips")
- "date" field is REQUIRED at the workout day level
- "exercise" must be an array of exercise objects
- Include 4-6 exercises per workout
- For cardio exercises with no weight, use empty string: "weight": ""

DIET ARRAY FORMAT (use today's date: 2026-01-15):
[
  {{
    "date": "2026-01-15",
    "foods": [
      {{
        "meal": "Breakfast",
        "title": "Descriptive meal title",
        "items": [
          "Food item 1",
          "Food item 2",
          "Food item 3"
        ],
        "nutrients": {{
          "calories": 620,
          "protein": 45,
          "carbs": 70,
          "fats": 18
        }}
      }}
    ]
  }}
]

CRITICAL DIET RULES:
- "date" field is REQUIRED at the diet day level
- "title" field is REQUIRED for each meal (e.g., "High-protein start", "Lean protein + carbs + veg")
- "items" field is REQUIRED (array of food items, not just a single "foods" array)
- "nutrients" field is REQUIRED with all four values: calories, protein, carbs, fats (all as integers)
- Include 3-4 meals per day (Breakfast, Lunch, Snack, Dinner)
- Calculate realistic nutrient values

EXAMPLE RESPONSE FOR WORKOUT REQUEST:
{{
  "message": "Perfect! Here's a beginner-friendly fat-loss workout plan tailored for you.",
  "workout": [
    {{
      "date": "2026-01-15",
      "exercise": [
        {{
          "name": "Leg Press (Machine)",
          "sets": 4,
          "reps": "10-12",
          "weight": "60-90 kg",
          "description": "Sit with your back flat on the pad, feet shoulder-width on the platform. Lower the sled until your knees are comfortably bent, then press up without locking your knees.",
          "pro_tips": [
            "Keep your lower back glued to the pad; don't let hips roll up.",
            "Control the lowering for 2-3 seconds; drive up smoothly."
          ]
        }},
        {{
          "name": "Treadmill Incline Walk",
          "sets": 1,
          "reps": "25-35 minutes",
          "weight": "",
          "description": "Walk at a brisk pace on an incline you can sustain while still breathing hard but controlled.",
          "pro_tips": [
            "Start around 4-6% incline and adjust so you can keep going steadily.",
            "Hold the rails only if needed for balance; aim to walk hands-free."
          ]
        }}
      ]
    }}
  ],
  "diet": [],
  "summary": "Male, 20 years old, 100 kg, height 4'5\\", fat-loss goal, beginner"
}}

EXAMPLE RESPONSE FOR DIET REQUEST:
{{
  "message": "Here's a structured day of eating designed for fat loss with proper nutrition.",
  "workout": [],
  "diet": [
    {{
      "date": "2026-01-15",
      "foods": [
        {{
          "meal": "Breakfast",
          "title": "High-protein start",
          "items": [
            "Whole eggs + egg whites omelet",
            "Oats cooked with milk",
            "Banana",
            "Cinnamon"
          ],
          "nutrients": {{
            "calories": 620,
            "protein": 45,
            "carbs": 70,
            "fats": 18
          }}
        }},
        {{
          "meal": "Lunch",
          "title": "Lean protein + carbs + veg",
          "items": [
            "Grilled chicken breast",
            "Basmati rice",
            "Mixed salad (lettuce, cucumber, tomato)",
            "Olive oil + lemon dressing"
          ],
          "nutrients": {{
            "calories": 720,
            "protein": 55,
            "carbs": 75,
            "fats": 20
          }}
        }}
      ]
    }}
  ],
  "summary": "Male, 20 years old, 100 kg, height 4'5\\", fat-loss goal, no dietary restrictions"
}}

Never include extra text outside JSON.
Never use markdown formatting.
Return ONLY the JSON object.
Ensure all required fields are present with correct names and structure.
"""


class AIPlanChatView(APIView):
    """Handle AI Plan chat requests with OpenAI integration."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Process user input and return AI-generated fitness advice.
        Creates or retrieves user's session and maintains conversation history.
        """
        # Validate request data
        serializer = AskRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "success": False,
                    "message": "Invalid request data",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        user_input = validated_data["user_input"]
        summary = validated_data.get("summary", "")
        workout = validated_data.get("workout", [])
        diet = validated_data.get("diet", [])

        try:
            # Get or create user's session (one session per user)
            session, created = AIPlanSession.objects.get_or_create(user=request.user)

            # Build conversation history from previous conversations
            conversation_history = ""
            previous_conversations = session.conversations.all()[
                :10
            ]  # Last 10 conversations

            if previous_conversations:
                for conv in reversed(list(previous_conversations)):
                    conversation_history += f"User: {conv.user_message}\n"
                    conversation_history += f"AI: {conv.ai_message}\n\n"
            else:
                conversation_history = "No previous conversation"

            # Prepare OpenAI request
            client = get_openai_client()

            formatted_prompt = SYSTEM_PROMPT.format(
                summary=summary or "No profile information yet",
                workout=(
                    json.dumps(workout, indent=2) if workout else "No workout plan yet"
                ),
                diet=json.dumps(diet, indent=2) if diet else "No diet plan yet",
                user_input=user_input,
                conversation_history=conversation_history,
            )

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using available model
                messages=[{"role": "system", "content": formatted_prompt}],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            ai_reply = response.choices[0].message.content.strip()

            # Parse AI response
            try:
                response_json = json.loads(ai_reply)
            except json.JSONDecodeError as e:
                return Response(
                    {
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "success": False,
                        "message": f"Invalid JSON response from AI: {str(e)}",
                        "raw_response": ai_reply,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            ai_message = response_json.get("message", "")
            response_workout = response_json.get("workout", [])
            response_diet = response_json.get("diet", [])
            response_summary = response_json.get("summary", summary)

            # Save conversation to database
            conversation = AIPlanConversation.objects.create(
                session=session,
                user_message=user_input,
                ai_message=ai_message,
                summary=response_summary,
                workout=response_workout if response_workout else [],
                diet=response_diet if response_diet else [],
            )

            # Prepare response
            response_data = {
                "session_id": str(session.id),
                "response": {
                    "message": ai_message,
                    "workout": response_workout,
                    "diet": response_diet,
                    "summary": response_summary,
                },
            }

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "success": True,
                    "message": "Chat processed successfully",
                    "data": response_data,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            # OpenAI API key not configured
            return Response(
                {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "success": False,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            # General error handling
            return Response(
                {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "success": False,
                    "message": f"An error occurred: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SessionDetailView(APIView):
    """Retrieve user's AI Plan session and conversation history."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the authenticated user's session with all conversations.
        """
        try:
            session = AIPlanSession.objects.get(user=request.user)
            serializer = SessionDetailSerializer(session)

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "success": True,
                    "message": "Session retrieved successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except AIPlanSession.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "success": False,
                    "message": "No session found for this user",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
