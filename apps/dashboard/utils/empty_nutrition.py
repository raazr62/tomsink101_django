
def empty_nutrition():
    def block(unit):
        return {
            "target": 0,
            "actual": 0,
            "difference": 0,
            "unit": unit,
            "status": "exact"
        }

    return {
        "protein": block("g"),
        "calories": block("kcal"),
        "carbs": block("g"),
        "fats": block("g"),
    }