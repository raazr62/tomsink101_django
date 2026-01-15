"""
Test script for AI Plan API endpoints.
Tests chat functionality, session management, and conversation history.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8007/api"
ACCESS_TOKEN = ""  # Add your JWT access token here

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


def test_chat_basic_question():
    """Test basic fitness question."""
    print("\n" + "=" * 60)
    print("Test 1: Basic Question - What is a plank exercise?")
    print("=" * 60)

    data = {"user_input": "What is a plank exercise?"}

    try:
        response = requests.post(f"{BASE_URL}/chat/", headers=headers, json=data)

        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(f"✓ Success: {result.get('message')}")
            session_id = result.get("data", {}).get("session_id")
            print(f"Session ID: {session_id}")
            ai_response = result.get("data", {}).get("response", {})
            print(f"AI Message: {ai_response.get('message')[:100]}...")
            return session_id
        else:
            print(f"✗ Error: {result}")
            return None

    except Exception as e:
        print(f"✗ Exception: {e}")
        return None


def test_chat_collect_info(session_id=None):
    """Test collecting user information."""
    print("\n" + "=" * 60)
    print("Test 2: Collect User Information")
    print("=" * 60)

    data = {
        "user_input": "I am 25 years old, weigh 80 kg, height 175 cm, and my goal is muscle gain"
    }

    try:
        response = requests.post(f"{BASE_URL}/chat/", headers=headers, json=data)

        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(f"✓ Success: {result.get('message')}")
            ai_response = result.get("data", {}).get("response", {})
            summary = ai_response.get("summary", "")
            print(f"AI Message: {ai_response.get('message')[:100]}...")
            print(f"Updated Summary: {summary}")
            return summary
        else:
            print(f"✗ Error: {result}")
            return None

    except Exception as e:
        print(f"✗ Exception: {e}")
        return None


def test_chat_workout_plan(summary):
    """Test requesting a workout plan."""
    print("\n" + "=" * 60)
    print("Test 3: Request Workout Plan")
    print("=" * 60)

    data = {"user_input": "Create a workout plan for muscle gain", "summary": summary}

    try:
        response = requests.post(f"{BASE_URL}/chat/", headers=headers, json=data)

        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(f"✓ Success: {result.get('message')}")
            ai_response = result.get("data", {}).get("response", {})
            workout = ai_response.get("workout", [])
            print(f"AI Message: {ai_response.get('message')[:100]}...")
            print(f"Workout days: {len(workout)}")

            if workout:
                for day in workout:
                    exercises = day.get("exercise", [])
                    print(
                        f"  - Date: {day.get('date', 'N/A')}, Exercises: {len(exercises)}"
                    )
                    for ex in exercises[:2]:  # Show first 2 exercises
                        print(
                            f"    • {ex.get('name', 'N/A')} - {ex.get('sets', 'N/A')} sets x {ex.get('reps', 'N/A')} reps"
                        )

            return workout
        else:
            print(f"✗ Error: {result}")
            return []

    except Exception as e:
        print(f"✗ Exception: {e}")
        return []


def test_chat_diet_plan(summary):
    """Test requesting a diet plan."""
    print("\n" + "=" * 60)
    print("Test 4: Request Diet Plan")
    print("=" * 60)

    data = {"user_input": "Give me a diet plan for muscle gain", "summary": summary}

    try:
        response = requests.post(f"{BASE_URL}/chat/", headers=headers, json=data)

        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(f"✓ Success: {result.get('message')}")
            ai_response = result.get("data", {}).get("response", {})
            diet = ai_response.get("diet", [])
            print(f"AI Message: {ai_response.get('message')[:100]}...")
            print(f"Diet days: {len(diet)}")

            if diet:
                for day in diet:
                    foods = day.get("foods", [])
                    print(f"  - Date: {day.get('date', 'N/A')}, Meals: {len(foods)}")
                    for meal in foods[:2]:  # Show first 2 meals
                        nutrients = meal.get("nutrients", {})
                        print(
                            f"    • {meal.get('meal', 'N/A')}: {meal.get('title', 'N/A')}"
                        )
                        print(
                            f"      Calories: {nutrients.get('calories', 'N/A')}, Protein: {nutrients.get('protein', 'N/A')}g"
                        )

            return diet
        else:
            print(f"✗ Error: {result}")
            return []

    except Exception as e:
        print(f"✗ Exception: {e}")
        return []


def test_modify_workout(summary, current_workout):
    """Test modifying existing workout."""
    print("\n" + "=" * 60)
    print("Test 5: Modify Workout - Add More Leg Exercises")
    print("=" * 60)

    data = {
        "user_input": "Add more leg exercises",
        "summary": summary,
        "workout": current_workout,
    }

    try:
        response = requests.post(f"{BASE_URL}/chat/", headers=headers, json=data)

        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(f"✓ Success: {result.get('message')}")
            ai_response = result.get("data", {}).get("response", {})
            updated_workout = ai_response.get("workout", [])
            print(f"AI Message: {ai_response.get('message')[:100]}...")
            print(f"Updated workout days: {len(updated_workout)}")

            if updated_workout:
                for day in updated_workout:
                    exercises = day.get("exercise", [])
                    print(f"  - Exercises: {len(exercises)}")
                    # Count leg exercises
                    leg_exercises = [
                        ex
                        for ex in exercises
                        if "leg" in ex.get("name", "").lower()
                        or "squat" in ex.get("name", "").lower()
                    ]
                    print(f"    Leg exercises: {len(leg_exercises)}")

            return updated_workout
        else:
            print(f"✗ Error: {result}")
            return []

    except Exception as e:
        print(f"✗ Exception: {e}")
        return []


def test_get_session():
    """Test retrieving session history."""
    print("\n" + "=" * 60)
    print("Test 6: Get Session History")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/sessions/", headers=headers)

        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(f"✓ Success: {result.get('message')}")
            data = result.get("data", {})
            print(f"Session ID: {data.get('id')}")
            print(f"User: {data.get('user_email')}")
            print(f"Conversation Count: {data.get('conversation_count')}")
            print(f"Created: {data.get('created_at')}")

            conversations = data.get("conversations", [])
            if conversations:
                print(f"\nRecent Conversations:")
                for i, conv in enumerate(conversations[:3], 1):  # Show first 3
                    print(f"  {i}. User: {conv.get('user_message')[:50]}...")
                    print(f"     AI: {conv.get('ai_message')[:50]}...")
                    print(f"     Created: {conv.get('created_at')}")
        else:
            print(f"✗ Error: {result}")

    except Exception as e:
        print(f"✗ Exception: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("AI PLAN API TEST SUITE")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")

    # Check if token is provided
    if not ACCESS_TOKEN:
        print("\n✗ ERROR: ACCESS_TOKEN is not set!")
        print("Please set your JWT access token in the script.")
        print("\nTo get a token:")
        print("1. Login via /api/login/ endpoint")
        print("2. Copy the access token from the response")
        print("3. Set ACCESS_TOKEN variable in this script")
        sys.exit(1)

    print(
        f"Token: {ACCESS_TOKEN[:20]}..."
        if len(ACCESS_TOKEN) > 20
        else "Token: [too short]"
    )
    print("=" * 60)

    # Run tests sequentially
    session_id = test_chat_basic_question()

    summary = test_chat_collect_info(session_id)

    if summary:
        workout = test_chat_workout_plan(summary)
        diet = test_chat_diet_plan(summary)

        if workout:
            test_modify_workout(summary, workout)

    test_get_session()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
