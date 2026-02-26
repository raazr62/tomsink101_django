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
from .models import (
    FitnessGoal, Workout, WeeklyStats, NutritionPlan, 
    CoachInsight, BodyWeightEntry, AchievementDefinition, UserAchievement
)
from django.db.models import Sum
from .serializers import (
    DashboardSerializer, FitnessGoalSerializer, WorkoutSerializer,
    WeeklyStatsSerializer, NutritionPlanSerializer, CoachInsightSerializer,
    BodyWeightPostSerializer, BodyWeightGetSerializer
)

from decimal import Decimal
from apps.dashboard.utils.empty_nutrition import empty_nutrition
from apps.dashboard.utils.weight import parse_weight_kg
from apps.task.models import Meal, DietPlan, Exercise
from django.db.models import Count, Q, F

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

        try: 
            user = request.user
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            # 1. Workouts
            workouts = Exercise.objects.filter(workout_plan__user=user)
            workouts_target = workouts.count() or 5
            workouts_completed = workouts.filter(status="completed").count()

            # Workout percentage
            workout_percentage = int((workouts_completed / workouts_target) * 100) if workouts_target > 0 else 0

            # 2. Nutritions
            nutrition = Meal.objects.filter(diet_plan__user=user)
            nutrition_target = nutrition.count()
            nutrition_completed = nutrition.filter(status="completed").count()

            # Nutrition percentage
            nutrition_percentage = int((nutrition_completed / nutrition_target) * 100) if nutrition_target > 0 else 0
            
            # 3. Overall streak
            streak = 0
            for i in range(0, 365):  # limit search to last year
                day = today - timedelta(days=i)
                
                # Check if user has any scheduled exercises for this day
                has_scheduled_exercise = Exercise.objects.filter(workout_plan__user=user, date=day).exists()
                
                # Check if user has any scheduled meals for this day
                has_scheduled_meal = Meal.objects.filter(diet_plan__user=user, date=day).exists()
                
                # If nothing scheduled for this day, skip it (don't break streak for rest days)
                if not has_scheduled_exercise and not has_scheduled_meal:
                    continue
                
                # Check if user completed at least one exercise
                did_workout = Exercise.objects.filter(workout_plan__user=user, date=day, status="completed").exists()
                
                # Check if user completed at least one meal
                did_meal = Meal.objects.filter(diet_plan__user=user, date=day, status="completed").exists()
                
                # Successful day: completed both exercise AND meal (if both are scheduled)
                if has_scheduled_exercise and has_scheduled_meal:
                    successful_day = did_workout and did_meal
                elif has_scheduled_exercise:
                    successful_day = did_workout
                elif has_scheduled_meal:
                    successful_day = did_meal
                else:
                    successful_day = False
                
                if successful_day:
                    streak += 1
                else:
                    break

            # 4. Success rate
            success_rate = int((workout_percentage + nutrition_percentage) / 2)

            # 5. Calories Burned
            MET = Decimal(6)  # Metabolic Equivalent of Task
            workout_duration = Decimal(0.125)  # Per workout duration in hours (7.5 minutes)
            weight = BodyWeightEntry.objects.filter(user=user).order_by('-created_at').first()
            
            calories = int(MET * weight.weight_kg * workout_duration) if weight else 0 # calories formula = METs x weight (kg) x time (hours)
            
            weekly_workouts_target = Exercise.objects.filter(workout_plan__user=user, date__range=(week_start, week_end)).count() or 5
            weekly_workout_completed = Exercise.objects.filter(workout_plan__user=user, date__range=(week_start, week_end), status="completed").count()

            calories_burned_target = weekly_workouts_target * calories  
            calories_burned_actual = weekly_workout_completed * calories

            # 6. Bodyweight comparison
            bodyweight_entries = BodyWeightEntry.objects.filter(user=user).order_by('-created_at')[:2]
            current_bodyweight = bodyweight_entries[0] if len(bodyweight_entries) > 0 else None
            previous_bodyweight = bodyweight_entries[1] if len(bodyweight_entries) > 1 else current_bodyweight

            # 7. Workout minutes
            workout_minutes_target = weekly_workouts_target * workout_duration * 60  # Convert hours to minutes
            workout_minutes_actual = weekly_workout_completed * workout_duration * 60

            # Persist weekly stats
            stats, created = WeeklyStats.objects.get_or_create(
                user=user,
                week_start_date=week_start,
                defaults={
                    'week_end_date': week_end
                }
            )

            stats.calories_burned = calories_burned_actual
            stats.nutrition_score = nutrition_percentage
            stats.workout_minutes = workout_minutes_actual
            stats.workouts_completed = weekly_workout_completed
            stats.save()

            response_data = {
                "summaryCards": [
                    {"type": "workouts", "value": workout_percentage, "unit": "%"},
                    {"type": "nutrition", "value": nutrition_percentage, "unit": "%"},
                    {"type": "streak", "value": streak, "unit": "days"},
                    {"type": "success_rate", "value": success_rate, "unit": "%"}
                ],
                "weeklyStats": {
                    "caloriesBurned": {"current": calories_burned_actual, "target": calories_burned_target, "unit": "kcal"},
                    "bodyWeight": {"current": float(current_bodyweight.weight_kg) if current_bodyweight else 0, "previous": float(previous_bodyweight.weight_kg) if previous_bodyweight else 0, "unit": "kg"},
                    "workoutMinutes": {"current": workout_minutes_actual, "target": workout_minutes_target, "unit": "min"},
                    "completedWorkouts": {"current": weekly_workout_completed, "target": weekly_workouts_target, "unit": "workouts"}
                }
            }

            return Response({
                "status": 200,
                "success": True,
                "message": "User workout stats fetched successfully",
                "data": response_data,
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": 500,
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                "status": 200,
                "success": True,
                "message": "No active diet plan found.",
                "data": {
                    "date": today,
                    "nutrition": empty_nutrition()
                }
            }, status=status.HTTP_200_OK)

        # Today meals (TARGET = all meals)
        all_meals = Meal.objects.filter(
            diet_plan=diet_plan,
            date=today
        ).exclude(date__isnull=True)

        # Completed meals only (ACTUAL)
        completed_meals = Meal.objects.filter(
            diet_plan=diet_plan,
            date=today,
            status="completed"
        )

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

# My Plan Stats
class MyPlanStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            # workout percentage
            completeted_exercise = Exercise.objects.filter(workout_plan__user=user, date__range=(week_start, week_end), status='completed').count()
            all_exercises = Exercise.objects.filter(workout_plan__user=user, date__range=(week_start, week_end)).count()
            weekly_percentage = int(completeted_exercise / all_exercises * 100) if all_exercises > 0 else 0
            
            # calories burned
            calories_burned_kcal = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().calories_burned if WeeklyStats.objects.filter(user=user, week_start_date=week_start).exists() else 0
            calories_difference = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().calories_burned - WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).first().calories_burned if WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).exists() else 0
            calories_difference_percentage = int((calories_difference / WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).first().calories_burned) * 100) if WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).exists() and WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).first().calories_burned > 0 else 0
            
            # nutrition percentage
            nutrition_percentage = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().nutrition_score if WeeklyStats.objects.filter(user=user, week_start_date=week_start).exists() else 0
            nutrition_percentage_difference = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().nutrition_score - WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).first().nutrition_score if WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).exists() else 0

            # active time
            active_time = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().workout_minutes if WeeklyStats.objects.filter(user=user, week_start_date=week_start).exists() else 0
            active_time_hours = round(active_time / 60, 1) if active_time > 0 else 0
            active_time_difference = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().workout_minutes - WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).first().workout_minutes if WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).exists() else 0
            active_time_difference_hours = round(active_time_difference / 60, 1) if active_time_difference > 0 else 0
            
            # workouts completed
            workouts_completed = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().workouts_completed if WeeklyStats.objects.filter(user=user, week_start_date=week_start).exists() else 0
            workouts_completed_difference = WeeklyStats.objects.filter(user=user, week_start_date=week_start).first().workouts_completed - WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).first().workouts_completed if WeeklyStats.objects.filter(user=user, week_start_date=week_start - timedelta(weeks=1)).exists() else 0

            data = {
                "weekly_progress": weekly_percentage,
                "calories_burned_kcal": calories_burned_kcal,
                "calories_difference_percentage": calories_difference_percentage,
                "nutrition_percentage": nutrition_percentage,
                "nutrition_percentage_difference": nutrition_percentage_difference,
                "active_time_hours": active_time_hours,
                "active_time_difference_hours": active_time_difference_hours,
                "workouts_completed": workouts_completed,
                "workouts_completed_difference": workouts_completed_difference,
            }

            return Response({
                "status": 200,
                "success": True,
                "message": "My Plan stats fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": 500,
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# BodyWeight
class BodyWeightView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        body_weight = BodyWeightEntry.objects.filter(user=request.user).all()
        
        if not body_weight:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "success": False,
                "message": "No body weight entries found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BodyWeightGetSerializer(body_weight, many=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "Body weight entries fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        
        # Check if user has a recent entry (within 7 days)
        last_entry = BodyWeightEntry.objects.filter(user=request.user).first()
        
        if last_entry:
            days_since_last = (timezone.now().date() - last_entry.created_at.date()).days
            
            if days_since_last < 7:
                days_remaining = 7 - days_since_last
                next_allowed_date = last_entry.created_at.date() + timedelta(days=7)
                
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "success": False,
                    "message": f"You can only post body weight once every 7 days. Please wait {days_remaining} more days.",
                    "data": {
                        "last_entry_date": last_entry.created_at.date().isoformat(),
                        "days_since_last": days_since_last,
                        "days_remaining": days_remaining,
                        "next_allowed_date": next_allowed_date.isoformat()
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation passed, create new entry
        serializer = BodyWeightPostSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            
            return Response({
                "status": status.HTTP_201_CREATED,
                "success": True,
                "message": "Body weight entry created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "success": False,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# User Achievements
class UserAchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            start_of_month = timezone.now().replace(day=1)
            end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # total earned (all time)
            total_earned = UserAchievement.objects.filter(user=user, status='earned').count()

            # Fetch achievement definitions
            calorie_crusher = AchievementDefinition.objects.filter(title="calorie crusher").first()
            strength_master = AchievementDefinition.objects.filter(title="strength master").first()
            marathon_runner = AchievementDefinition.objects.filter(title="marathon runner").first()
            active_days = AchievementDefinition.objects.filter(title="active days").first()
            workout_finisher = AchievementDefinition.objects.filter(title="workout finisher").first()
            perfect_week = AchievementDefinition.objects.filter(title="perfect week").first()
            month = timezone.now().strftime("%B")

            # Calorie Crusher
            cc_icon = calorie_crusher.icon.url if calorie_crusher and calorie_crusher.icon else None
            cc_title = calorie_crusher.title if calorie_crusher else "Calorie Crusher"
            cc_description = calorie_crusher.description if calorie_crusher else ""
            cc_actual_value_raw = Meal.objects.filter(diet_plan__user=user, status="completed", created_at__gte=start_of_month, created_at__lte=end_of_month).aggregate(total_calories=Sum('calories'))['total_calories'] or 0
            cc_target_value = calorie_crusher.target_value if calorie_crusher else 0
            cc_actual_value = min(cc_actual_value_raw, cc_target_value)
            cc_status = "earned" if cc_actual_value == cc_target_value and calorie_crusher else "in_progress"
            
            # Save achievement status if earned
            if cc_actual_value == cc_target_value and calorie_crusher:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=calorie_crusher,
                    period_start=start_of_month,
                    defaults={'status': 'earned', 'earned_at': timezone.now(), 'actual_value': cc_actual_value}
                )
                if not created and user_achievement.status != 'earned':
                    user_achievement.status = 'earned'
                    user_achievement.earned_at = timezone.now()
                    user_achievement.actual_value = cc_actual_value
                    user_achievement.save()

            # Strength Master
            sm_icon = strength_master.icon.url if strength_master and strength_master.icon else None
            sm_title = strength_master.title if strength_master else "Strength Master"
            sm_description = strength_master.description if strength_master else ""
            sm_actual_value_raw = Exercise.objects.filter(workout_plan__user=user, status="completed", exercise_type="strength", created_at__gte=start_of_month, created_at__lte=end_of_month).count()
            sm_target_value = strength_master.target_value if strength_master else 0
            sm_actual_value = min(sm_actual_value_raw, sm_target_value)
            sm_status = "earned" if sm_actual_value == sm_target_value and strength_master else "in_progress"
            
            # Save achievement status if earned
            if sm_actual_value == sm_target_value and strength_master:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=strength_master,
                    period_start=start_of_month,
                    defaults={'status': 'earned', 'earned_at': timezone.now(), 'actual_value': sm_actual_value}
                )
                if not created and user_achievement.status != 'earned':
                    user_achievement.status = 'earned'
                    user_achievement.earned_at = timezone.now()
                    user_achievement.actual_value = sm_actual_value
                    user_achievement.save()

            # Marathon Runner
            mr_icon = marathon_runner.icon.url if marathon_runner and marathon_runner.icon else None
            mr_title = marathon_runner.title if marathon_runner else "Marathon Runner"
            mr_description = marathon_runner.description if marathon_runner else ""
            mr_actual_value_raw = 0 # No Marathon Run
            mr_target_value = marathon_runner.target_value if marathon_runner else 0
            mr_actual_value = min(mr_actual_value_raw, mr_target_value)
            mr_status = "earned" if mr_actual_value == mr_target_value and marathon_runner else "in_progress"
            
            # Save achievement status if earned
            if mr_actual_value == mr_target_value and marathon_runner:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=marathon_runner,
                    period_start=start_of_month,
                    defaults={'status': 'earned', 'earned_at': timezone.now(), 'actual_value': mr_actual_value}
                )
                if not created and user_achievement.status != 'earned':
                    user_achievement.status = 'earned'
                    user_achievement.earned_at = timezone.now()
                    user_achievement.actual_value = mr_actual_value
                    user_achievement.save()

            # Active Days
            ad_icon = active_days.icon.url if active_days and active_days.icon else None
            ad_title = active_days.title if active_days else "Active Days"
            ad_description = active_days.description if active_days else ""
            ad_actual_value_raw=(
                Exercise.objects.filter(
                    workout_plan__user=user,
                    date__gte=start_of_month,
                    date__lte=end_of_month,
                )
                .values("date")  
                .annotate(
                    total_ex=Count("id"),
                    completed_ex=Count("id", filter=Q(status="completed")),
                )
                .filter(completed_ex=F("total_ex"))
                .count()
            )
            ad_target_value = active_days.target_value if active_days else 0
            ad_actual_value = min(ad_actual_value_raw, ad_target_value)
            ad_status = "earned" if ad_actual_value == ad_target_value and active_days else "in_progress"
            
            # Save achievement status if earned
            if ad_actual_value == ad_target_value and active_days:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=active_days,
                    period_start=start_of_month,
                    defaults={'status': 'earned', 'earned_at': timezone.now(), 'actual_value': ad_actual_value}
                )
                if not created and user_achievement.status != 'earned':
                    user_achievement.status = 'earned'
                    user_achievement.earned_at = timezone.now()
                    user_achievement.actual_value = ad_actual_value
                    user_achievement.save()

            # Workout Finisher
            wf_icon = workout_finisher.icon.url if workout_finisher and workout_finisher.icon else None
            wf_title = workout_finisher.title if workout_finisher else "Workout Finisher"
            wf_description = workout_finisher.description if workout_finisher else ""
            wf_actual_value_raw = Exercise.objects.filter(workout_plan__user=user, status="completed", created_at__gte=start_of_month, created_at__lte=end_of_month).count()
            wf_target_value = workout_finisher.target_value if workout_finisher else 0
            wf_actual_value = min(wf_actual_value_raw, wf_target_value)
            wf_status = "earned" if wf_actual_value == wf_target_value and workout_finisher else "in_progress"

            # Save achievement status if earned
            if wf_actual_value == wf_target_value and workout_finisher:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=workout_finisher,
                    period_start=start_of_month,
                    defaults={'status': 'earned', 'earned_at': timezone.now(), 'actual_value': wf_actual_value}
                )
                if not created and user_achievement.status != 'earned':
                    user_achievement.status = 'earned'
                    user_achievement.earned_at = timezone.now()
                    user_achievement.actual_value = wf_actual_value
                    user_achievement.save()

            # Perfect Week
            pw_icon = perfect_week.icon.url if perfect_week and perfect_week.icon else None
            pw_title = perfect_week.title if perfect_week else "Perfect Week"
            pw_description = perfect_week.description if perfect_week else ""
            pw_actual_value_raw = Exercise.objects.filter(
                workout_plan__user=user, 
                status="completed", 
                created_at__gte=start_of_month, 
                created_at__lte=end_of_month
                ).count() 
            pw_target_value = perfect_week.target_value if perfect_week else 0
            pw_actual_value = min(pw_actual_value_raw, pw_target_value)
            pw_status = "earned" if pw_actual_value == pw_target_value and perfect_week else "in_progress"
            
            # Save achievement status if earned
            if pw_actual_value == pw_target_value and perfect_week:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=perfect_week,
                    period_start=start_of_month,
                    defaults={'status': 'earned', 'earned_at': timezone.now(), 'actual_value': pw_actual_value}
                )
                if not created and user_achievement.status != 'earned':
                    user_achievement.status = 'earned'
                    user_achievement.earned_at = timezone.now()
                    user_achievement.actual_value = pw_actual_value
                    user_achievement.save()

            data  = [{
                "total_earned": total_earned,
                "calorie_crusher": {
                    "icon": cc_icon,
                    "title": cc_title,
                    "description": cc_description,
                    "month": month,
                    "actual_value": cc_actual_value,
                    "target_value": cc_target_value,
                    "status": cc_status,
                },
                "strength_master": {
                    "icon": sm_icon,
                    "title": sm_title,
                    "description": sm_description,
                    "month": month,
                    "actual_value": sm_actual_value,
                    "target_value": sm_target_value,
                    "status": sm_status,
                },
                "marathon_runner": {
                    "icon": mr_icon,
                    "title": mr_title,
                    "description": mr_description,
                    "month": month,
                    "actual_value": mr_actual_value,
                    "target_value": mr_target_value,
                    "status": mr_status,
                },
                "active_days": {
                    "icon": ad_icon,
                    "title": ad_title,
                    "description": ad_description,
                    "month": month,
                    "actual_value": ad_actual_value,
                    "target_value": ad_target_value,
                    "status": ad_status,
                },
                "workout_finisher": {
                    "icon": wf_icon,
                    "title": wf_title,
                    "description": wf_description,  
                    "month": month,
                    "actual_value": wf_actual_value,
                    "target_value": wf_target_value,
                    "status": wf_status,
                },
                "perfect_week": {
                    "icon": pw_icon,
                    "title": pw_title,
                    "description": pw_description,
                    "month": month,
                    "actual_value": pw_actual_value,
                    "target_value": pw_target_value,
                    "status": pw_status,
                },
                
            }]

            return Response({
                "status": 200,
                "success": True,
                "message": "User achievements fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": 500,
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Personal Records
class PersonalRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            start_of_month = timezone.now().replace(day=1)
            end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            date_format = "%b %d, %Y"
            
            # bench press max weight
            bp_qs = Exercise.objects.filter(
                workout_plan__user=user, 
                name__icontains="bench press",
                status="completed",
                date__gte=start_of_month, 
                date__lte=end_of_month
            ).order_by('-date')

            bp_weight = 0

            for exercise in bp_qs:
                parsed_weight = parse_weight_kg(self, exercise.weight)

                if parsed_weight is not None:
                    if bp_weight is None or parsed_weight > bp_weight:
                        bp_weight = parsed_weight

            # bench press max weight date
            achievement_date_qs = bp_qs.first().updated_at if bp_qs.exists() else 0
            bp_achievement_date = achievement_date_qs.strftime(date_format) if achievement_date_qs else 0 

            # squat max weight
            squat_qs = Exercise.objects.filter(
                workout_plan__user=user, 
                name__icontains="squat",
                status="completed",
                date__gte=start_of_month, 
                date__lte=end_of_month
            ).order_by('-date')

            squat_weight = 0

            for exercise in squat_qs:
                parsed_weight = parse_weight_kg(self, exercise.weight)

                if parsed_weight is not None:
                    if squat_weight is None or parsed_weight > squat_weight:
                        squat_weight = parsed_weight

            # deadlift max weight date
            achievement_date_qs = squat_qs.first().updated_at if squat_qs.exists() else 0
            squat_achievement_date = achievement_date_qs.strftime(date_format) if achievement_date_qs else 0

            # squat max weight date
            achievement_date_qs = squat_qs.first().updated_at if squat_qs.exists() else 0
            squat_achievement_date = achievement_date_qs.strftime(date_format) if achievement_date_qs else 0

            # deadlift max weight
            deadlift_qs = Exercise.objects.filter(
                workout_plan__user=user, 
                name__icontains="deadlift",
                status="completed",
                date__gte=start_of_month, 
                date__lte=end_of_month
            ).order_by('-date')

            deadlift_weight = 0

            for exercise in deadlift_qs:
                parsed_weight = parse_weight_kg(self, exercise.weight)

                if parsed_weight is not None:
                    if deadlift_weight is None or parsed_weight > deadlift_weight:
                        deadlift_weight = parsed_weight

            # deadlift max weight date
            achievement_date_qs = deadlift_qs.first().updated_at if deadlift_qs.exists() else 0
            deadlift_achievement_date = achievement_date_qs.strftime(date_format) if achievement_date_qs else 0 



            data = [{
                "bench_press": {
                    "achievement_date": bp_achievement_date,
                    "value": bp_weight,
                    "unit": "kg"
                },
                "squat": {
                    "achievement_date": squat_achievement_date,
                    "value": squat_weight,
                    "unit": "kg"
                },
                "deadlift": {
                    "achievement_date": deadlift_achievement_date,
                    "value": deadlift_weight,
                    "unit": "kg"
                },
            }]

            return Response({
                "status": 200,
                "success": True,
                "message": "Personal records fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": 500,
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





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
        
        # Get last two bodyweight entries for comparison
        bodyweight_entries = BodyWeightEntry.objects.filter(user=user).order_by('-created_at')[:2]
        current_bodyweight = bodyweight_entries[0] if len(bodyweight_entries) > 0 else None
        previous_bodyweight = bodyweight_entries[1] if len(bodyweight_entries) > 1 else None
        
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
                    "current": float(current_bodyweight.weight_kg) if current_bodyweight else None,
                    "previous": float(previous_bodyweight.weight_kg) if previous_bodyweight else None,
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




