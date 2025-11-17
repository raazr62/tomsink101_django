import json
import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()
client = OpenAI()

app = FastAPI(title="AI Fitness Coach API")

SESSIONS_FILE = "chat_sessions.json"


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


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_input: str


@app.post("/chat")
def chat(request: ChatRequest):
    sessions = load_sessions()

    session_id = get_or_create_session(sessions, request.session_id)

    conversation_text = ""
    for m in sessions[session_id]:
        conversation_text += f"User: {m['user_message']}\nAI: {m['ai_message']}\n"
    conversation_text += f"User: {request.user_input}\nAI:"

    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation_text}
            ],
            temperature=0.8,
        )

        ai_reply = response.output[0].content[0].text.strip()

        # Remove markdown code blocks if present
        ai_reply = re.sub(r'^```json\s*', '', ai_reply)
        ai_reply = re.sub(r'^```\s*', '', ai_reply)
        ai_reply = re.sub(r'\s*```$', '', ai_reply)
        ai_reply = ai_reply.strip()

        print("Cleaned AI Reply:", ai_reply)
        
        response_json = json.loads(ai_reply)
        ai_message = response_json.get("message", "")
        diet = response_json.get("diet", [])
        workout = response_json.get("workout", [])
        summary = response_json.get("summary", "")
        
        conversation_entry = {
            "user_message": request.user_input,
            "ai_message": ai_message,
        }
        
        if workout:
            conversation_entry["workout"] = workout
        if diet:
            conversation_entry["diet"] = diet
        if summary:
            conversation_entry["summary"] = summary
        
        sessions[session_id].append(conversation_entry)
        save_sessions(sessions)

        return {
            "session_id": session_id,
            "response": {
                "message": ai_message,
                "workout": workout,
                "diet": diet,
                "summary": summary
            }
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
