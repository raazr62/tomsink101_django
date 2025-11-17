import json
import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

app = FastAPI(title="AI Fitness Coach API")

SESSIONS_FILE = "workout_history.json"


def load_sessions():
    """Load all chat sessions from file."""
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_sessions(sessions):
    """Save all chat sessions to file."""
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def get_or_create_session(sessions, session_id=None):
    """Return existing session if found, otherwise create a new one."""
    if session_id and session_id in sessions:
        return session_id
    new_id = session_id or str(uuid.uuid4())
    sessions[new_id] = []
    return new_id


system_prompt = """
You are a professional workout coach and AI assistant.
You help users with their workouts, fitness goals, and plans.
You NEVER answer non-fitness questions.

You must ALWAYS respond in **strict JSON** format like this:
{{
  "message": "natural reply text here",
  "workout": []
}}

User Profile Summary: {summary}

Current Workout Plan:
{workout}

User Question: {user_input}

Previous Conversation:
{conversation_history}

IMPORTANT RULES:
1. For basic questions about exercises (like "What is Plank?", "How to do Push-ups?"), provide helpful explanation in "message" field and keep "workout" as empty array.
2. For workout modification requests (like "Add more cardio", "Replace plank with another exercise"), provide the COMPLETE updated workout plan in "workout" array.
3. Always consider the user's profile summary when giving advice.
4. Workout array format: [{{"exercise": "name", "sets": 3, "reps": "10-12"}}] or [{{"exercise": "name", "sets": 3, "duration": "30 seconds"}}]

Never include extra text outside JSON.
Never include markdown or explanations.
Just return pure JSON.
"""

class AskRequest(BaseModel):
    session_id: str | None = None
    user_input: str
    summary: str 
    workout: list[dict]


@app.post("/ask")
def chat(request: AskRequest):
    sessions = load_sessions()
    session_id = get_or_create_session(sessions, request.session_id)

    # Build conversation history
    conversation_history = ""
    for m in sessions[session_id]:
        conversation_history += f"User: {m.get('user_message', '')}\nAI: {m.get('ai_message', '')}\n"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.format(
                        summary=request.summary,
                        workout=json.dumps(request.workout, indent=2), 
                        user_input=request.user_input,
                        conversation_history=conversation_history if conversation_history else "No previous conversation"
                    )
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        ai_reply = response.choices[0].message.content.strip()
        print("AI Reply:", ai_reply)
        
        response_json = json.loads(ai_reply)
        ai_message = response_json.get("message", "")
        workout = response_json.get("workout", [])
        
        conversation_entry = {
            "user_message": request.user_input,
            "ai_message": ai_message,
        }
        
        if workout:
            conversation_entry["workout"] = workout
        
        sessions[session_id].append(conversation_entry)
        save_sessions(sessions)

        return {
            "session_id": session_id,
            "response": {
                "message": ai_message,
                "workout": workout,
            }
        }

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw AI response: {ai_reply}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(e)}")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))