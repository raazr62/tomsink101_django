from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from calendar import monthrange
from .models import WorkoutPlan, Exercise, DietPlan, Meal, DailyProgress, WorkoutReview
from apps.manageai.models import ChatSession, ChatMessage
from .serializers import (
    ReplaceMealSerializer,
    WorkoutPlanSerializer,
    ExerciseSerializer,
    DietPlanSerializer,
    MealSerializer,
    DailyProgressSerializer,
    ExerciseUpdateSerializer,
    MealUpdateSerializer,
    WorkoutReviewSerializer,
    WorkoutReviewCreateSerializer,
    WorkoutReviewOptionsSerializer
)


class WorkoutPlanListView(APIView):
    """
    API View for listing all workout plans for the authenticated user.
    
    GET: List all workout plans
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workout_plans = WorkoutPlan.objects.filter(user=request.user)
        serializer = WorkoutPlanSerializer(workout_plans, many=True)
        return Response({   
                            "status": status.HTTP_200_OK,
                            "message": "Workout plans retrieved successfully",
                            "data": serializer.data},
                            status=status.HTTP_200_OK
                        )  


class WorkoutPlanDetailView(APIView):
    """
    API View for retrieving, updating, or deleting a specific workout plan.
    
    GET: Retrieve workout plan details
    PATCH: Update workout plan
    DELETE: Delete workout plan
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id):
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
        serializer = WorkoutPlanSerializer(workout_plan)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Workout plan retrieved successfully",
            "data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, plan_id):
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
        serializer = WorkoutPlanSerializer(workout_plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Workout plan updated successfully",
                "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, plan_id):
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
        workout_plan.delete()
        return Response({
            "status": status.HTTP_204_NO_CONTENT,
            "message": "Workout plan deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ExerciseUpdateView(APIView):
    """
    API View for updating exercise progress.
    
    PATCH: Update exercise status and completed sets
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, id=exercise_id, workout_plan__user=request.user)
        serializer = ExerciseUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            if 'completed_sets' in serializer.validated_data:
                exercise.completed_sets = serializer.validated_data['completed_sets']
            if 'status' in serializer.validated_data:
                exercise.status = serializer.validated_data['status']
            if 'notes' in serializer.validated_data:
                exercise.notes = serializer.validated_data['notes']
            
            exercise.save()
            response_serializer = ExerciseSerializer(exercise)
            return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Exercise updated successfully",
                    "data": response_serializer.data}, status=status.HTTP_200_OK)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DietPlanListView(APIView):
    """
    API View for listing all diet plans for the authenticated user.
    
    GET: List all diet plans
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        diet_plans = DietPlan.objects.filter(user=request.user)
        serializer = DietPlanSerializer(diet_plans, many=True)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Diet plans retrieved successfully",
            "data": serializer.data}, status=status.HTTP_200_OK)


class DietPlanDetailView(APIView):
    """
    API View for retrieving, updating, or deleting a specific diet plan.
    
    GET: Retrieve diet plan details
    PATCH: Update diet plan
    DELETE: Delete diet plan
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id):
        diet_plan = get_object_or_404(DietPlan, id=plan_id, user=request.user)
        serializer = DietPlanSerializer(diet_plan)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Diet plan retrieved successfully",
            "data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, plan_id):
        diet_plan = get_object_or_404(DietPlan, id=plan_id, user=request.user)
        serializer = DietPlanSerializer(diet_plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Diet plan updated successfully",
                "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, plan_id):
        diet_plan = get_object_or_404(DietPlan, id=plan_id, user=request.user)
        diet_plan.delete()
        return Response({
            "status": status.HTTP_204_NO_CONTENT,
            "message": "Diet plan deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class MealUpdateView(APIView):
    """
    API View for updating meal status.
    
    PATCH: Update meal completion status
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, meal_id):
        meal = get_object_or_404(Meal, id=meal_id, diet_plan__user=request.user)
        serializer = MealUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            if 'status' in serializer.validated_data:
                meal.status = serializer.validated_data['status']
            if 'notes' in serializer.validated_data:
                meal.notes = serializer.validated_data['notes']
            
            meal.save()
            response_serializer = MealSerializer(meal)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Meal updated successfully",
                "data": response_serializer.data}, status=status.HTTP_200_OK)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ReplaceMealView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, meal_id):
        meal = get_object_or_404(Meal, id=meal_id, diet_plan__user=request.user)
        serializer = ReplaceMealSerializer(meal, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 200,
                "success": True,
                "message": "Meal replaced successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "status": 400,
            "success": False,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, meal_id):
        meal = get_object_or_404(Meal, id=meal_id, diet_plan__user=request.user)
        serializer = ReplaceMealSerializer(meal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 200,
                "success": True,
                "message": "Meal updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "status": 400,
            "success": False,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class DailyProgressView(APIView):
    """
    API View for tracking daily progress.
    
    GET: Get daily progress for a specific date
    POST: Create or update daily progress
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date', timezone.now().date())
        progress = DailyProgress.objects.filter(user=request.user, date=date_str)
        serializer = DailyProgressSerializer(progress, many=True)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Daily progress retrieved successfully",
            "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DailyProgressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Daily progress created successfully",
                "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class TaskDashboardView(APIView):
    """
    API View for getting a dashboard overview of all tasks.
    
    GET: Get overview of workout plans, diet plans, and progress
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get active workout and diet plans
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
        
        # Get today's progress
        today = timezone.now().date()
        today_progress = DailyProgress.objects.filter(user=request.user, date=today).first()
        
        response_data = {
            'active_workout_plan': WorkoutPlanSerializer(active_workout).data if active_workout else None,
            'active_diet_plan': DietPlanSerializer(active_diet).data if active_diet else None,
            'today_progress': DailyProgressSerializer(today_progress).data if today_progress else None,
            'total_workout_plans': WorkoutPlan.objects.filter(user=request.user).count(),
            'total_diet_plans': DietPlan.objects.filter(user=request.user).count(),
        }
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Dashboard data retrieved successfully",
            "data": response_data
        }, status=status.HTTP_200_OK)


class WeeklyStatsView(APIView):
    """
    API View for getting weekly statistics shown in the top cards.
    
    GET: Get calories burned, nutrition, active time, workouts completed
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range for this week
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get active plans
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
        
        # Calculate stats for this week
        weekly_progress = DailyProgress.objects.filter(
            user=request.user,
            date__gte=week_start,
            date__lte=week_end
        )
        
        # Workouts completed this week
        workouts_completed = weekly_progress.aggregate(
            total=Sum('exercises_completed')
        )['total'] or 0
        
        # Meals completed this week
        meals_completed = weekly_progress.aggregate(
            total=Sum('meals_completed')
        )['total'] or 0
        
        # Calculate nutrition (from completed meals this week)
        if active_diet:
            completed_meals = Meal.objects.filter(
                diet_plan=active_diet,
                status='completed',
                updated_at__date__gte=week_start,
                updated_at__date__lte=week_end
            )
            total_nutrition = completed_meals.aggregate(
                calories=Sum('calories'),
                protein=Sum('protein'),
                carbs=Sum('carbs'),
                fats=Sum('fats')
            )
        else:
            total_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
        
        # Estimate calories burned (rough calculation based on exercises)
        calories_burned = workouts_completed * 350  # Rough estimate per workout
        
        # Estimate active time (rough calculation)
        active_time_hours = workouts_completed * 0.75  # Roughly 45 min per workout
        
        response_data = {
            'calories_burned': calories_burned,
            'calories_burned_change': '+12%',  # You can calculate this from previous week
            'nutrition': total_nutrition.get('calories', 0),
            'nutrition_change': '+15%',
            'active_time': round(active_time_hours, 1),
            'active_time_change': '+1.2h',
            'workouts_completed': workouts_completed,
            'workouts_completed_change': '+3',
            'week_progress': 65  # Overall progress percentage
        }
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Weekly stats retrieved successfully",
            "data": response_data
        }, status=status.HTTP_200_OK)


class WorkoutCalendarView(APIView):
    """
    API View for getting calendar data for a specific month.
    
    GET: Get workout calendar with completion status for each day
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get month and year from query params (default to current month)
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        # Get first and last day of the month
        first_day = datetime(year, month, 1).date()
        last_day_num = monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num).date()
        
        # Get all daily progress for this month
        progress_data = DailyProgress.objects.filter(
            user=request.user,
            date__gte=first_day,
            date__lte=last_day
        ).values('date', 'exercises_completed', 'meals_completed')
        
        # Create a dict for quick lookup
        progress_dict = {p['date']: p for p in progress_data}
        
        # Get active workout and diet plans
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
        expected_exercises = active_workout.total_exercises if active_workout else 0
        expected_meals = active_diet.total_meals if active_diet else 4
        
        # Build calendar data by checking scheduled exercises/meals for each date
        calendar_data = {}
        for day in range(1, last_day_num + 1):
            current_date = datetime(year, month, day).date()
            progress = progress_dict.get(current_date, None)

            # Count scheduled and completed exercises/meals for this specific date
            if active_workout:
                expected_exercises_day = active_workout.exercises.filter(date=current_date).count()
                completed_exercises_day = active_workout.exercises.filter(date=current_date, status='completed').count()
            else:
                expected_exercises_day = 0
                completed_exercises_day = 0

            if active_diet:
                expected_meals_day = active_diet.meals.filter(date=current_date).count()
                completed_meals_day = active_diet.meals.filter(date=current_date, status='completed').count()
            else:
                expected_meals_day = 0
                completed_meals_day = 0

            # Prefer DailyProgress counts when present (for backward compatibility),
            # otherwise use counts derived from scheduled items.
            exercises_done = progress['exercises_completed'] if progress is not None else completed_exercises_day
            meals_done = progress['meals_completed'] if progress is not None else completed_meals_day

            # Determine status
            if expected_exercises_day == 0 and expected_meals_day == 0:
                # No scheduled items for this date -> rest
                status_type = 'null'
            else:
                if exercises_done >= expected_exercises_day and meals_done >= expected_meals_day:
                    status_type = 'complete'
                elif exercises_done > 0 or meals_done > 0:
                    status_type = 'incomplete'
                else:
                    status_type = 'incomplete'

            # Use date as key in the dictionary
            calendar_data[current_date.isoformat()] = {
                'day': day,
                'status': status_type,
                'exercises_completed': exercises_done,
                'meals_completed': meals_done
            }
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Workout calendar retrieved successfully",
            "data": {
                'year': year,
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B %Y'),
                **calendar_data
            }
        }, status=status.HTTP_200_OK)


class DailyWorkoutDetailView(APIView):
    """
    API View for getting detailed workout information for a specific date.
    
    GET: Get exercises and meals for a specific date with completion status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        # Parse date
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get active workout and diet plans. If there is no active plan, try to find
        # any plan that has items scheduled for the target date.
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        active_diet = DietPlan.objects.filter(user=request.user, status='active').first()

        if not active_workout:
            active_workout = WorkoutPlan.objects.filter(user=request.user, exercises__date=target_date).distinct().first()
        if not active_diet:
            active_diet = DietPlan.objects.filter(user=request.user, meals__date=target_date).distinct().first()

        if not active_workout and not active_diet:
            return Response({
                'error': 'No active workout or diet plan found for the requested date'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get exercises with their completion status (only those scheduled for the date)
        exercises_data = []
        if active_workout:
            exercises = active_workout.exercises.filter(date=target_date).order_by('order')
            for exercise in exercises:
                exercises_data.append({
                    'id': str(exercise.id),
                    'name': exercise.name,
                    'sets': exercise.sets,
                    'reps': exercise.reps,
                    'description': exercise.description,
                    'tips': exercise.pro_tips or [],
                    'completed_sets': exercise.completed_sets,
                    'status': exercise.status,
                    'completion_percentage': exercise.completion_percentage,
                    'order': exercise.order
                })

        # Get meals with their completion status (only those scheduled for the date)
        meals_data = []
        if active_diet:
            meals = active_diet.meals.filter(date=target_date).order_by('order')
            for meal in meals:
                meals_data.append({
                    'id': str(meal.id),
                    'meal_type': meal.meal_type,
                    'title': meal.title,
                    'items': meal.items,
                    'calories': meal.calories,
                    'protein': meal.protein,
                    'carbs': meal.carbs,
                    'fats': meal.fats,
                    'status': meal.status,
                    'order': meal.order
                })

        # Get daily progress for this date
        daily_progress = DailyProgress.objects.filter(
            user=request.user,
            date=target_date
        ).first()

        # Calculate today's nutrition totals from completed meals (use meal.date)
        if active_diet:
            completed_meals_today = Meal.objects.filter(
                diet_plan=active_diet,
                status='completed',
                date=target_date
            )
            nutrition_totals = completed_meals_today.aggregate(
                calories=Sum('calories'),
                protein=Sum('protein'),
                carbs=Sum('carbs'),
                fats=Sum('fats')
            )
        else:
            nutrition_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
        
        # Calculate completion progress
        total_exercises = len(exercises_data)
        completed_exercises = sum(1 for e in exercises_data if e['status'] == 'completed')
        
        total_meals = len(meals_data)
        completed_meals = sum(1 for m in meals_data if m['status'] == 'completed')

        # Compute target nutrition totals for the requested date (only meals scheduled for that date)
        if active_diet:
            target_meals_qs = Meal.objects.filter(diet_plan=active_diet, date=target_date)
            target_nutrition_agg = target_meals_qs.aggregate(
                calories=Sum('calories'),
                protein=Sum('protein'),
                carbs=Sum('carbs'),
                fats=Sum('fats')
            )
            target_calories = target_nutrition_agg.get('calories') or 0
            target_protein = target_nutrition_agg.get('protein') or 0
            target_carbs = target_nutrition_agg.get('carbs') or 0
            target_fats = target_nutrition_agg.get('fats') or 0
        else:
            target_calories = target_protein = target_carbs = target_fats = 0
        
        response_data = {
            'date': target_date.isoformat(),
            'workout_plan': {
                'id': str(active_workout.id) if active_workout else None,
                'name': active_workout.name if active_workout else None,
                'exercises': exercises_data,
                'total_exercises': total_exercises,
                'completed_exercises': completed_exercises,
                'progress_percentage': round((completed_exercises / total_exercises * 100), 2) if total_exercises > 0 else 0
            },
            'diet_plan': {
                'id': str(active_diet.id) if active_diet else None,
                'name': active_diet.name if active_diet else None,
                'meals': meals_data,
                'total_meals': total_meals,
                'completed_meals': completed_meals,
                'nutrition_totals': {
                    'calories': nutrition_totals.get('calories', 0) or 0,
                    'protein': nutrition_totals.get('protein', 0) or 0,
                    'carbs': nutrition_totals.get('carbs', 0) or 0,
                    'fats': nutrition_totals.get('fats', 0) or 0
                },
                'target_nutrition': {
                    'calories': target_calories,
                    'protein': target_protein,
                    'carbs': target_carbs,
                    'fats': target_fats
                }
            },
            'daily_progress': DailyProgressSerializer(daily_progress).data if daily_progress else None
        }
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Dashboard data retrieved successfully",
            "data": response_data
        }, status=status.HTTP_200_OK)


class ExerciseSetToggleView(APIView):
    """
    API View for toggling individual set completion for an exercise.
    
    POST: Toggle a specific set as complete/incomplete
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, id=exercise_id, workout_plan__user=request.user)
        set_number = request.data.get('set_number', 1)
        
        # Toggle set completion
        if set_number <= exercise.sets:
            if exercise.completed_sets < set_number:
                exercise.completed_sets = set_number
            elif exercise.completed_sets == set_number:
                exercise.completed_sets = set_number - 1
            
            # Update status based on completion
            if exercise.completed_sets == 0:
                exercise.status = 'pending'
            elif exercise.completed_sets < exercise.sets:
                exercise.status = 'in_progress'
            else:
                exercise.status = 'completed'
            
            exercise.save()
            
            # Update daily progress
            today = timezone.now().date()
            workout_plan = exercise.workout_plan
            
            # Count completed exercises for active plan
            completed_count = workout_plan.exercises.filter(status='completed').count()
            
            # Get active diet plan
            active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
            
            daily_progress, created = DailyProgress.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    'exercises_completed': completed_count,
                    'workout_plan': workout_plan,
                    'diet_plan': active_diet
                }
            )
            if not created:
                daily_progress.exercises_completed = completed_count
                daily_progress.workout_plan = workout_plan
                if active_diet:
                    daily_progress.diet_plan = active_diet
                daily_progress.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Exercise set toggled successfully",
                "data": {
                    'id': str(exercise.id),
                    'completed_sets': exercise.completed_sets,
                    'status': exercise.status,
                    'completion_percentage': exercise.completion_percentage
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "success": False,
            "message": "Invalid set number",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)


class MealToggleView(APIView):
    """
    API View for toggling meal completion status.
    
    POST: Toggle meal as complete/incomplete
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, meal_id):
        meal = get_object_or_404(Meal, id=meal_id, diet_plan__user=request.user)
        
        # Toggle meal status
        if meal.status == 'completed':
            meal.status = 'pending'
        else:
            meal.status = 'completed'
        
        meal.save()
        
        # Update daily progress
        today = timezone.now().date()
        diet_plan = meal.diet_plan
        
        # Count completed meals for active plan
        completed_count = diet_plan.meals.filter(status='completed').count()
        
        # Get active workout plan
        active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
        
        daily_progress, created = DailyProgress.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={
                'meals_completed': completed_count,
                'diet_plan': diet_plan,
                'workout_plan': active_workout
            }
        )
        if not created:
            daily_progress.meals_completed = completed_count
            daily_progress.diet_plan = diet_plan
            if active_workout:
                daily_progress.workout_plan = active_workout
            daily_progress.save()
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Meal toggled successfully",
            "data": {
                'id': str(meal.id),
                'status': meal.status,
                'is_completed': meal.is_completed
            }
        }, status=status.HTTP_200_OK)


class ResetAllTaskDataView(APIView):
    """
    API View for resetting all task-related data for the authenticated user.
    This will delete all workout plans, diet plans, exercises, meals, and daily progress.
    
    DELETE: Reset all task data (requires confirmation)
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        
        # Get confirmation from request
        confirm = request.data.get('confirm', False)
        
        if not confirm:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "success": False,
                "message": "Please confirm deletion by sending 'confirm': true in the request body.",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Count items before deletion
            workout_plans_count = WorkoutPlan.objects.filter(user=user).count()
            diet_plans_count = DietPlan.objects.filter(user=user).count()
            daily_progress_count = DailyProgress.objects.filter(user=user).count()
            chat_sessions_count = ChatSession.objects.filter(user=user).count()
            chat_messages_count = ChatMessage.objects.filter(session__user=user).count()
            
            # Delete all task data for the user
            # Due to CASCADE relationships, deleting plans will also delete exercises and meals
            WorkoutPlan.objects.filter(user=user).delete()
            DietPlan.objects.filter(user=user).delete()
            DailyProgress.objects.filter(user=user).delete()
            # Delete all chat data for the user
            # Due to CASCADE relationships, deleting sessions will also delete messages
            ChatSession.objects.filter(user=user).delete()
            
            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "All task and chat data has been reset successfully",
                "data": {
                    "deleted_items": {
                        "workout_plans": workout_plans_count,
                        "diet_plans": diet_plans_count,
                        "daily_progress": daily_progress_count,
                        "chat_sessions": chat_sessions_count,
                        "chat_messages": chat_messages_count
                    },
                    "reset_at": timezone.now()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "success": False,
                "message": "Failed to reset task data",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkoutReviewOptionsView(APIView):
    """
    API View for getting workout review form options.
    
    GET: Get all available options for the review form
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        options = {
            'difficulty_options': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in WorkoutReview.DIFFICULTY_CHOICES
            ],
            'target_hit_options': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in WorkoutReview.TARGET_HIT_CHOICES
            ],
            'energy_level_options': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in WorkoutReview.ENERGY_LEVEL_CHOICES
            ],
            'body_feeling_options': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in WorkoutReview.BODY_FEELING_CHOICES
            ],
            'satisfaction_options': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in WorkoutReview.SATISFACTION_CHOICES
            ],
        }
        
        serializer = WorkoutReviewOptionsSerializer(options)
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Workout review options retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class WorkoutReviewView(APIView):
    """
    API View for creating and retrieving workout reviews.
    
    GET: Get review for a specific workout plan
    POST: Submit a review for a workout plan
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id):
        """Get existing review for a workout plan."""
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
        
        try:
            review = WorkoutReview.objects.get(workout_plan=workout_plan, user=request.user)
            serializer = WorkoutReviewSerializer(review)
            
            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Workout review retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except WorkoutReview.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "success": False,
                "message": "No review found for this workout plan",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, plan_id):
        """Submit or update a review for a workout plan."""
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
        
        # Check if review already exists
        try:
            review = WorkoutReview.objects.get(workout_plan=workout_plan, user=request.user)
            # Update existing review
            serializer = WorkoutReviewCreateSerializer(
                review, 
                data=request.data, 
                context={'request': request},
                partial=True
            )
        except WorkoutReview.DoesNotExist:
            # Create new review
            serializer = WorkoutReviewCreateSerializer(
                data=request.data, 
                context={'request': request}
            )
        
        if serializer.is_valid():
            serializer.save(user=request.user, workout_plan=workout_plan)
            
            return Response({
                "status": status.HTTP_201_CREATED,
                "success": True,
                "message": "Workout review submitted successfully",
                "data": WorkoutReviewSerializer(
                    WorkoutReview.objects.get(workout_plan=workout_plan, user=request.user)
                ).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "success": False,
            "message": "Invalid review data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
