import re

def parse_weight_kg(self, weight_text: str):
        if not weight_text:
            return None

        text = weight_text.replace("–", "-").lower()

        nums = re.findall(r"\d+(?:\.\d+)?", text)
        if not nums:
            return None

        max_val = max(float(n) for n in nums)

        # If dumbbells each → convert to total load
        if "each" in text and "dumbbell" in text:
            max_val = max_val * 2

        return max_val