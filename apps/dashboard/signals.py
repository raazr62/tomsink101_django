from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.task.models import WorkoutPlan, Exercise
from .models import BodyWeightEntry, CoachInsight
import re
import json


@receiver(post_save, sender=WorkoutPlan)
def create_bodyweight_initial(sender, instance, created, **kwargs):
    if created and not BodyWeightEntry.objects.filter(user=instance.user).exists():
        weight_kg = 0  # Default weight
        
        if instance.summary:
            # Try to extract weight from summary
            weight_kg = extract_weight_from_summary(instance.summary)
        
        # Create the body weight entry
        if weight_kg > 0:
            BodyWeightEntry.objects.create(user=instance.user, weight_kg=weight_kg)

# Helper function to extract weight from summary text
def extract_weight_from_summary(summary):
    if not summary:
        return 0

    # if the summary happens to be a JSON blob, load and inspect common keys
    try:
        data = json.loads(summary)
        weight_keys = [
            'weight', 'current_weight', 'currentWeight', 'initial_weight',
            'initialWeight', 'weight_kg', 'body_weight', 'bodyWeight'
        ]
        for key in weight_keys:
            if key in data and data[key]:
                try:
                    weight = float(data[key])
                except (ValueError, TypeError):
                    continue
                if 30 <= weight <= 300:  # normal human range in kg
                    return weight
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # fallback to regex searching the text
    patterns = [
        r'(?:current\s*)?weight[:\s]*(\d+\.?\d*)\s*kg',
        r'(?:initial\s*)?weight[:\s]*(\d+\.?\d*)\s*kg',
        r'body\s*weight[:\s]*(\d+\.?\d*)\s*kg',
        r'(\d+\.?\d*)\s*kg',
        r'(?:current\s*)?weight[:\s]*(\d+\.?\d*)',
    ]
    summary_lower = summary.lower()
    for pattern in patterns:
        match = re.search(pattern, summary_lower, re.IGNORECASE)
        if match:
            try:
                weight = float(match.group(1))
            except (ValueError, IndexError):
                continue
            if 30 <= weight <= 300:
                return weight

    return 0


# create an insight whenever an exercise is completed
@receiver(post_save, sender='task.Exercise')
def exercise_completed_insight(sender, instance, created, **kwargs):
    # only care about completed status
    if getattr(instance, 'status', None) != 'completed':
        return

    user = instance.workout_plan.user
    msg = f"Great job! You finished the exercise '{instance.name}'. Keep going!"
    # avoid duplicate; you could also store a flag on Exercise
    if CoachInsight.objects.filter(user=user, message=msg).exists():
        return

    CoachInsight.objects.create(
        user=user,
        message=msg,
        insight_type='exercise'
    )
    
    # previously this code attempted to use a variable named `summary` which
    # wasn't defined in this scope.  pull the text off the instance instead and
    # delegate to the reusable helper above.
    summary = getattr(instance, 'summary', None)
    weight_kg = extract_weight_from_summary(summary)

    # if we found a reasonable weight, store it
    if weight_kg > 0:
        BodyWeightEntry.objects.create(user=user, weight_kg=weight_kg)

    # note: the earlier message creation and duplicate check remain untouched
    # (they occur before this patch in the function)
