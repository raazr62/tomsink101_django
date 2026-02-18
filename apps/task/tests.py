from django.test import TestCase

# Create your tests here.


# class WorkoutCalendarView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         # Get month and year from query params (default to current month)
#         year = int(request.query_params.get('year', timezone.now().year))
#         month = int(request.query_params.get('month', timezone.now().month))
        
#         # Get first and last day of the month
#         first_day = datetime(year, month, 1).date()
#         last_day_num = monthrange(year, month)[1]
#         last_day = datetime(year, month, last_day_num).date()
        
#         # Get all daily progress for this month
#         progress_data = DailyProgress.objects.filter(
#             user=request.user,
#             date__gte=first_day,
#             date__lte=last_day
#         ).values('date', 'exercises_completed', 'meals_completed')
        
#         # Create a dict for quick lookup
#         progress_dict = {p['date']: p for p in progress_data}
        
#         # Get active workout and diet plans
#         active_workout = WorkoutPlan.objects.filter(user=request.user, status='active').first()
#         active_diet = DietPlan.objects.filter(user=request.user, status='active').first()
#         expected_exercises = active_workout.total_exercises if active_workout else 0
#         expected_meals = active_diet.total_meals if active_diet else 4
        
#         # Build calendar data by checking scheduled exercises/meals for each date
#         calendar_data = {}
#         for day in range(1, last_day_num + 1):
#             current_date = datetime(year, month, day).date()
#             progress = progress_dict.get(current_date, None)

#             # Count scheduled and completed exercises/meals for this specific date
#             if active_workout:
#                 expected_exercises_day = active_workout.exercises.filter(date=current_date).count()
#                 completed_exercises_day = active_workout.exercises.filter(date=current_date, status='completed').count()
#             else:
#                 expected_exercises_day = 0
#                 completed_exercises_day = 0

#             # if active_diet:
#             #     expected_meals_day = active_diet.meals.filter(date=current_date).count()
#             #     completed_meals_day = active_diet.meals.filter(date=current_date, status='completed').count()
#             # else:
#             #     expected_meals_day = 0
#             #     completed_meals_day = 0

#             # Prefer DailyProgress counts when present (for backward compatibility),
#             # otherwise use counts derived from scheduled items.
#             exercises_done = progress['exercises_completed'] if progress is not None else completed_exercises_day
#             meals_done = progress['meals_completed'] if progress is not None else 0

#             # Determine status
#             if expected_exercises_day == 0:
#                 # No scheduled items for this date -> rest
#                 status_type = 'null'
#             else:
#                 if exercises_done >= expected_exercises_day:
#                     status_type = 'complete'
#                 elif exercises_done > 0:
#                     status_type = 'incomplete'
#                 else:
#                     status_type = 'incomplete'

#             # Use date as key in the dictionary
#             calendar_data[current_date.isoformat()] = {
#                 'day': day,
#                 'status': status_type,
#                 'exercises_completed': exercises_done,
#                 'meals_completed': meals_done
#             }
        
#         return Response({
#             "status": status.HTTP_200_OK,
#             "success": True,
#             "message": "Workout calendar retrieved successfully",
#             "data": {
#                 'year': year,
#                 'month': month,
#                 'month_name': datetime(year, month, 1).strftime('%B %Y'),
#                 **calendar_data
#             }
#         }, status=status.HTTP_200_OK)