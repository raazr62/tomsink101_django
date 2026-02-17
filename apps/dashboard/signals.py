from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.task.models import WorkoutPlan
from .models import BodyWeightEntry
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
    
    try:
        # Try parsing as JSON first
        data = json.loads(summary)
        
        # Check common weight keys
        weight_keys = ['weight', 'current_weight', 'currentWeight', 'initial_weight', 
                      'initialWeight', 'weight_kg', 'body_weight', 'bodyWeight']
        
        for key in weight_keys:
            if key in data and data[key]:
                weight = float(data[key])
                if 30 <= weight <= 300:  # Reasonable weight range in kg
                    return weight
    
    except (json.JSONDecodeError, ValueError, TypeError):
        # If not JSON or parsing fails, try text extraction
        pass
    
    # Try regex patterns for text extraction
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
                if 30 <= weight <= 300:  # Reasonable weight range in kg
                    return weight
            except (ValueError, IndexError):
                continue
    
    return 0