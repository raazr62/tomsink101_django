from django.shortcuts import render, HttpResponse
from apps.system_setting.models import SystemColor
from apps.task.models import Exercise, WorkoutPlan
from apps.users.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import FitnessGoal, Workout, WeeklyStats, NutritionPlan, CoachInsight
from django.db.models import Sum
from .serializers import (
    DashboardSerializer, FitnessGoalSerializer, WorkoutSerializer,
    WeeklyStatsSerializer, NutritionPlanSerializer, CoachInsightSerializer
)

from apps.task.models import Meal, DietPlan

# Welcome
class WelcomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Get user name from user profile
        user_name = user.profile.name if hasattr(user, 'profile') and user.profile.name else user.email.split('@')[0]

        # Get today's workout
        today_workout = Exercise.objects.filter(workout_plan__user=user, workout_plan__status='active', date=today).order_by('order')
        
        # Calculate program statistics from exercises
        active_workout_plan = WorkoutPlan.objects.filter(user=user, status='active').first()
        
        goal_duration_weeks = 0
        current_week = 0
        progress_percent = 0
        
        if active_workout_plan:
            exercises = active_workout_plan.exercises.all()
            if exercises.exists():
                # Get earliest and latest exercise dates
                first_exercise_date = exercises.order_by('date').first().date
                last_exercise_date = exercises.order_by('-date').first().date
                
                if first_exercise_date and last_exercise_date:
                    # Calculate total weeks (difference between first and last exercise date)
                    total_days = (last_exercise_date - first_exercise_date).days + 1
                    goal_duration_weeks = (total_days + 6) // 7  # Round up to weeks
                    
                    # Calculate current week (which week of the program we're in)
                    if today >= first_exercise_date:
                        days_passed = (today - first_exercise_date).days + 1
                        current_week = min((days_passed + 6) // 7, goal_duration_weeks)  # Round up, but not exceed total
                    else:
                        current_week = 0
                    
                    # Calculate progress percentage
                    if goal_duration_weeks > 0:
                        progress_percent = int((current_week / goal_duration_weeks) * 100)
        
        # Calculate day number based on workout plan start date
        day_number = None
        workout_title = None
        if today_workout:
            first_exercise = today_workout.first()
            workout_plan = first_exercise.workout_plan
            # Get the earliest exercise date (start date of the plan)
            first_exercise_date = workout_plan.exercises.order_by('date').first().date
            if first_exercise_date:
                day_number = (today - first_exercise_date).days + 1
            workout_title = f"{first_exercise.name} • Day {day_number}" if day_number else first_exercise.name

        # Build response
        response_data = {
            "user": {
                "id": user.id,
                "Name": user_name,
            },
            "program": {
                "goalDurationWeeks": goal_duration_weeks,
                "currentWeek": current_week,
                "progressPercent": progress_percent,
            },
            "todayWorkout": {
                "title": workout_title,
                "exerciseCount": f"{today_workout.count() if today_workout else None} Exercises",
            } if today_workout else None
        }
        
        return Response({
            "status": 200,
            "success": True,
            "message": "Welcome data fetched successfully",
            "data": response_data,
            }, status=status.HTTP_200_OK)

# User Workout Stats
class UserWorkoutStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Workouts for the week
        workouts = Workout.objects.filter(user=user, scheduled_date__range=(week_start, week_end))
        workouts_target = workouts.count() or 5
        workouts_completed = workouts.filter(is_completed=True).count()

        # Workout percentage
        workout_percentage = int((workouts_completed / workouts_target) * 100) if workouts_target else 0

        # Aggregates
        calories_burned_total = workouts.filter(is_completed=True).aggregate(total=Sum('calories_burned'))['total'] or 0
        workout_minutes_total = workouts.filter(is_completed=True).aggregate(total=Sum('duration_minutes'))['total'] or 0

        # Nutrition score: average of daily macro compliance (0-100)
        nutrition_plans = NutritionPlan.objects.filter(user=user, date__range=(week_start, week_end)).order_by('date')
        day_scores = []
        for plan in nutrition_plans:
            protein_ratio = min(plan.protein_g / plan.protein_target_g, 1) if plan.protein_target_g else 0
            calories_ratio = min(plan.calories / plan.calories_target, 1) if plan.calories_target else 0
            fat_ratio = min(plan.fat_g / plan.fat_target_g, 1) if plan.fat_target_g else 0
            carbs_ratio = min(plan.carbs_g / plan.carbs_target_g, 1) if plan.carbs_target_g else 0
            day_score = (protein_ratio + calories_ratio + fat_ratio + carbs_ratio) / 4
            day_scores.append(day_score)

        nutrition_percentage = int((sum(day_scores) / len(day_scores)) * 100) if day_scores else 0

        # Overall streak: consecutive days up to today where user met either workout or nutrition threshold
        streak = 0
        for i in range(0, 365):  # limit search to last year
            day = today - timedelta(days=i)
            did_workout = Workout.objects.filter(user=user, scheduled_date=day, is_completed=True).exists()
            day_plan = NutritionPlan.objects.filter(user=user, date=day).first()
            day_score = 0
            if day_plan:
                p = min(day_plan.protein_g / day_plan.protein_target_g, 1) if day_plan.protein_target_g else 0
                c = min(day_plan.calories / day_plan.calories_target, 1) if day_plan.calories_target else 0
                f = min(day_plan.fat_g / day_plan.fat_target_g, 1) if day_plan.fat_target_g else 0
                cb = min(day_plan.carbs_g / day_plan.carbs_target_g, 1) if day_plan.carbs_target_g else 0
                day_score = (p + c + f + cb) / 4

            successful_day = did_workout or (day_plan and day_score >= 0.8)
            if successful_day:
                streak += 1
            else:
                break

        # Success rate: simple average of workout and nutrition percentages
        success_rate = int((workout_percentage + nutrition_percentage) / 2)

        # Persist weekly stats
        stats, created = WeeklyStats.objects.get_or_create(
            user=user,
            week_start_date=week_start,
            defaults={
                'week_end_date': week_end
            }
        )

        stats.workouts_completed = workouts_completed
        stats.workouts_target = workouts_target
        stats.nutrition_score = nutrition_percentage
        stats.overall_streak = streak
        stats.success_rate = success_rate
        stats.calories_burned = calories_burned_total
        stats.workout_minutes = workout_minutes_total
        stats.save()

        # Previous week bodyweight for comparison
        previous_week_start = week_start - timedelta(days=7)
        previous_week_stats = WeeklyStats.objects.filter(user=user, week_start_date=previous_week_start).first()
        previous_bodyweight = previous_week_stats.bodyweight_kg if previous_week_stats and previous_week_stats.bodyweight_kg else None

        response_data = {
            "summaryCards": [
                {"type": "workouts", "value": workout_percentage, "unit": "%"},
                {"type": "nutrition", "value": nutrition_percentage, "unit": "%"},
                {"type": "streak", "value": streak, "unit": "days"},
                {"type": "success_rate", "value": success_rate, "unit": "%"}
            ],
            "weeklyStats": {
                "caloriesBurned": {"current": stats.calories_burned, "target": stats.calories_target, "unit": "kcal"},
                "bodyWeight": {"current": float(stats.bodyweight_kg) if stats.bodyweight_kg else None, "previous": float(previous_bodyweight) if previous_bodyweight else None, "unit": "kg"},
                "workoutMinutes": {"current": stats.workout_minutes, "target": stats.workout_minutes_target, "unit": "min"},
                "completedWorkouts": {"current": stats.workouts_completed, "target": stats.workouts_target, "unit": "workouts"}
            }
        }

        return Response({
            "status": 200,
            "success": True,
            "message": "User workout stats fetched successfully",
            "data": response_data,
            }, status=status.HTTP_200_OK)

# Daily Nutrition Plan
class NutritionPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        # Active diet plan
        diet_plan = DietPlan.objects.filter(
            user=user,
            status="active"
        ).first()

        if not diet_plan:
            return Response({
                "status": 404,
                "success": False,
                "message": "No active diet plan found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Today meals (TARGET = all meals)
        all_meals = Meal.objects.filter(
            diet_plan=diet_plan,
            date=today
        ).exclude(date__isnull=True)

        # Completed meals only (ACTUAL)
        completed_meals = all_meals.filter(status="completed")

        # Target intake (planned)
        target = {
            "protein": sum(m.protein for m in all_meals),
            "calories": sum(m.calories for m in all_meals),
            "carbs": sum(m.carbs for m in all_meals),
            "fats": sum(m.fats for m in all_meals),
        }

        # Actual intake (completed)
        actual = {
            "protein": sum(m.protein for m in completed_meals),
            "calories": sum(m.calories for m in completed_meals),
            "carbs": sum(m.carbs for m in completed_meals),
            "fats": sum(m.fats for m in completed_meals),
        }

        # Nutrition block builder
        def build_nutrition(key, unit):
            diff = actual[key] - target[key]
            return {
                "target": target[key],
                "actual": actual[key],
                "difference": diff,
                "unit": unit,
                "status": (
                    "above" if diff > 0 else
                    "below" if diff < 0 else
                    "exact"
                )
            }

        # Final response data
        data = {
            "date": today,
            "nutrition": {
                "protein": build_nutrition("protein", "g"),
                "calories": build_nutrition("calories", "kcal"),
                "carbs": build_nutrition("carbs", "g"),
                "fats": build_nutrition("fats", "g"),
            }
        }

        return Response({
            "status": 200,
            "success": True,
            "message": "Daily nutrition plan fetched successfully",
            "data": data
        }, status=status.HTTP_200_OK)











# Admin Dashboard
def dashboard_callback(request, context):
    now = timezone.now()

    start_of_month = now.replace(day=1)
    total_subscribers = 20
    total_new_subscriptions = 5
    total_income = 1000

    if now.month == 12:
        start_of_next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        start_of_next_month = now.replace(month=now.month + 1, day=1)

    system_color = SystemColor.get_instance().code

    context.update(
        {
            "system_color": system_color,
            "total_users": User.objects.count(),
            "total_subscriptions": total_subscribers,
            "total_income": total_income,
            "total_new_subscriptions": total_new_subscriptions,
            "current_month_signups": User.objects.filter(
                created_at__gte=start_of_month,
                created_at__lt=start_of_next_month
            ).count(),
            "admins": User.objects.filter(is_staff=True).count(),
            "supper_admins": User.objects.filter(is_superuser=True).count(),
            "data": [
                User.objects.filter(
                    created_at__year=datetime.now().year,
                    created_at__month=m
                ).count() for m in range(1, 13)
            ]
        }
    )

    return context

# Fitness Dashboard API
class FitnessDashboardView(APIView):
    """
    Main dashboard endpoint that returns all fitness tracking data
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Get or create current fitness goal
        fitness_goal = FitnessGoal.objects.filter(
            user=user, 
            is_active=True
        ).first()
        
        if not fitness_goal:
            # Create default goal if none exists
            start_date = today
            end_date = start_date + timedelta(weeks=12)
            fitness_goal = FitnessGoal.objects.create(
                user=user,
                title=f"{user.profile.name}'s Fitness Journey" if hasattr(user, 'profile') and user.profile.name else "Your Fitness Journey",
                total_weeks=12,
                current_week=1,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
        
        # Get today's workout
        today_workout = Workout.objects.filter(
            user=user,
            scheduled_date=today
        ).first()
        
        # Get or create current week stats
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        current_week_stats = WeeklyStats.objects.filter(
            user=user,
            week_start_date=week_start
        ).first()
        
        if not current_week_stats:
            current_week_stats = WeeklyStats.objects.create(
                user=user,
                week_start_date=week_start,
                week_end_date=week_end,
                workouts_completed=0,
                workouts_target=5,
                nutrition_score=0,
                overall_streak=0,
                success_rate=0,
                calories_burned=0,
                calories_target=1890,
                bodyweight_kg=None,
                bodyweight_target_kg=None,
                workout_minutes=0,
                workout_minutes_target=125
            )
        
        # Get or create today's nutrition plan
        today_nutrition = NutritionPlan.objects.filter(
            user=user,
            date=today
        ).first()
        
        if not today_nutrition:
            today_nutrition = NutritionPlan.objects.create(
                user=user,
                date=today,
                protein_g=0,
                protein_target_g=140,
                calories=0,
                calories_target=2200,
                fat_g=0,
                fat_target_g=70,
                carbs_g=0,
                carbs_target_g=300
            )
        
        # Get latest unread coach insight
        latest_coach_insight = CoachInsight.objects.filter(
            user=user,
            is_read=False
        ).first()
        
        # Get user name
        user_name = user.profile.name if hasattr(user, 'profile') and user.profile.name else user.email.split('@')[0]
        
        # Get previous week bodyweight for comparison
        previous_week_start = week_start - timedelta(days=7)
        previous_week_stats = WeeklyStats.objects.filter(
            user=user,
            week_start_date=previous_week_start
        ).first()
        previous_bodyweight = previous_week_stats.bodyweight_kg if previous_week_stats and previous_week_stats.bodyweight_kg else None
        
        # Build response in the requested structure
        response_data = {
            "user": {
                "id": user.id,
                "firstName": user_name,
            },
            "program": {
                "goalDurationWeeks": fitness_goal.total_weeks,
                "currentWeek": fitness_goal.current_week,
                "progressPercent": fitness_goal.progress_percentage,
            },
            "todayWorkout": {
                "title": today_workout.title if today_workout else None,
                "focus": today_workout.focus_area if today_workout else None,
                "exerciseCount": today_workout.exercises_count if today_workout else None,
            } if today_workout else None,
            "summaryCards": [
                {
                    "type": "workouts",
                    "value": current_week_stats.workout_percentage,
                    "unit": "%"
                },
                {
                    "type": "nutrition",
                    "value": current_week_stats.nutrition_score,
                    "unit": "%"
                },
                {
                    "type": "streak",
                    "value": current_week_stats.overall_streak,
                    "unit": "days"
                },
                {
                    "type": "success_rate",
                    "value": current_week_stats.success_rate,
                    "unit": "%"
                }
            ],
            "weeklyStats": {
                "caloriesBurned": {
                    "current": current_week_stats.calories_burned,
                    "target": current_week_stats.calories_target,
                    "unit": "kcal"
                },
                "bodyWeight": {
                    "current": float(current_week_stats.bodyweight_kg) if current_week_stats.bodyweight_kg else None,
                    "previous": float(previous_bodyweight) if previous_bodyweight else None,
                    "unit": "kg"
                },
                "workoutMinutes": {
                    "current": current_week_stats.workout_minutes,
                    "target": current_week_stats.workout_minutes_target,
                    "unit": "min"
                },
                "completedWorkouts": {
                    "current": current_week_stats.workouts_completed,
                    "target": current_week_stats.workouts_target,
                    "unit": "workouts"
                }
            },
            "coachInsight": {
                "title": "Coach Insight",
                "message": latest_coach_insight.message if latest_coach_insight else None
            } if latest_coach_insight else None,
            "nutritionPlan": {
                "dailyTargets": {
                    "protein": {
                        "target": today_nutrition.protein_target_g,
                        "current": today_nutrition.protein_g,
                        "unit": "g",
                        "status": f"+{today_nutrition.protein_difference}g" if today_nutrition.protein_difference > 0 else f"{today_nutrition.protein_difference}g"
                    },
                    "calories": {
                        "target": today_nutrition.calories_target,
                        "current": today_nutrition.calories,
                        "unit": "kcal",
                        "status": f"+{today_nutrition.calories_difference}" if today_nutrition.calories_difference > 0 else f"{today_nutrition.calories_difference}"
                    },
                    "fat": {
                        "target": today_nutrition.fat_target_g,
                        "current": today_nutrition.fat_g,
                        "unit": "g",
                        "status": f"+{today_nutrition.fat_difference}g" if today_nutrition.fat_difference > 0 else f"{today_nutrition.fat_difference}g"
                    },
                    "carbs": {
                        "target": today_nutrition.carbs_target_g,
                        "current": today_nutrition.carbs_g,
                        "unit": "g",
                        "status": f"+{today_nutrition.carbs_difference}g" if today_nutrition.carbs_difference > 0 else f"{today_nutrition.carbs_difference}g"
                    }
                }
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class WorkoutListCreateView(APIView):
    """
    List all workouts or create a new workout
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workouts = Workout.objects.filter(user=request.user)
        
        # Optional filters
        is_completed = request.query_params.get('is_completed')
        if is_completed is not None:
            workouts = workouts.filter(is_completed=is_completed.lower() == 'true')
        
        date_from = request.query_params.get('date_from')
        if date_from:
            workouts = workouts.filter(scheduled_date__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            workouts = workouts.filter(scheduled_date__lte=date_to)
        
        serializer = WorkoutSerializer(workouts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WorkoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkoutDetailView(APIView):
    """
    Retrieve, update or delete a workout
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Workout.objects.get(pk=pk, user=user)
        except Workout.DoesNotExist:
            return None

    def get(self, request, pk):
        workout = self.get_object(pk, request.user)
        if not workout:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WorkoutSerializer(workout)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        workout = self.get_object(pk, request.user)
        if not workout:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WorkoutSerializer(workout, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # If workout is marked as completed, update weekly stats
            if request.data.get('is_completed') and not workout.is_completed:
                self._update_weekly_stats(request.user, workout)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        workout = self.get_object(pk, request.user)
        if not workout:
            return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)
        
        workout.delete()
        return Response({'message': 'Workout deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    def _update_weekly_stats(self, user, workout):
        """Update weekly stats when a workout is completed"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        week_stats, created = WeeklyStats.objects.get_or_create(
            user=user,
            week_start_date=week_start,
            defaults={
                'week_end_date': week_start + timedelta(days=6)
            }
        )
        
        week_stats.workouts_completed += 1
        week_stats.calories_burned += workout.calories_burned
        week_stats.workout_minutes += workout.duration_minutes
        week_stats.save()


class NutritionUpdateView(APIView):
    """
    Update today's nutrition data
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get nutrition data for a specific date or today"""
        date_str = request.query_params.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            date = timezone.now().date()
        
        nutrition = NutritionPlan.objects.filter(user=request.user, date=date).first()
        if not nutrition:
            return Response({'error': 'No nutrition data for this date'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        serializer = NutritionPlanSerializer(nutrition)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update nutrition data"""
        today = timezone.now().date()
        
        nutrition, created = NutritionPlan.objects.get_or_create(
            user=request.user,
            date=today
        )
        
        serializer = NutritionPlanSerializer(nutrition, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WeeklyStatsView(APIView):
    """
    Get weekly statistics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get stats for current week or specific week"""
        date_str = request.query_params.get('week_start')
        
        if date_str:
            try:
                week_start = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        stats = WeeklyStats.objects.filter(
            user=request.user,
            week_start_date=week_start
        ).first()
        
        if not stats:
            return Response({'error': 'No stats available for this week'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        serializer = WeeklyStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update weekly stats"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        stats, created = WeeklyStats.objects.get_or_create(
            user=request.user,
            week_start_date=week_start,
            defaults={
                'week_end_date': week_start + timedelta(days=6)
            }
        )
        
        serializer = WeeklyStatsSerializer(stats, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CoachInsightListView(APIView):
    """
    List coach insights
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        insights = CoachInsight.objects.filter(user=request.user)
        
        # Filter by read status
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            insights = insights.filter(is_read=is_read.lower() == 'true')
        
        serializer = CoachInsightSerializer(insights, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new coach insight"""
        serializer = CoachInsightSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CoachInsightDetailView(APIView):
    """
    Mark coach insight as read
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            insight = CoachInsight.objects.get(pk=pk, user=request.user)
        except CoachInsight.DoesNotExist:
            return Response({'error': 'Insight not found'}, status=status.HTTP_404_NOT_FOUND)
        
        insight.is_read = True
        insight.save()
        
        serializer = CoachInsightSerializer(insight)
        return Response(serializer.data, status=status.HTTP_200_OK)


