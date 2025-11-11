from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import NotificationPreference
from .serializers import (
    NotificationPreferenceSerializer, 
    NotificationPreferenceUpdateSerializer,
    BulkUpdateSerializer
)


class NotificationPreferenceView(APIView):
    """
    Get the authenticated user's notification preferences.
    If preferences don't exist, they will be created with default values.
    
    GET /api/notifications/preferences/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        try:
            # Get or create notification preferences for the user
            preferences, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )
            
            serializer = NotificationPreferenceSerializer(preferences)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Notification preferences retrieved successfully.' if not created else 'Notification preferences created with default settings.',
                'data': serializer.data
            })
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve notification preferences.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationPreferenceUpdateView(APIView):
    """
    Update the authenticated user's notification preferences.
    Supports partial updates (PATCH) and full updates (PUT).
    
    PUT/PATCH /api/notifications/preferences/update/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def put(self, request):
        return self._update_preferences(request, partial=False)
    
    def patch(self, request):
        return self._update_preferences(request, partial=True)
    
    def _update_preferences(self, request, partial=False):
        try:
            # Get or create notification preferences
            preferences, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )
            
            serializer = NotificationPreferenceUpdateSerializer(
                preferences, 
                data=request.data, 
                partial=partial
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # Return full data using the read serializer
                full_serializer = NotificationPreferenceSerializer(preferences)
                
                return Response({
                    'status': status.HTTP_200_OK,
                    'success': True,
                    'message': 'Notification preferences updated successfully.',
                    'data': full_serializer.data
                })
            
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'Failed to update notification preferences.',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'An error occurred while updating preferences.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationBulkActionView(APIView):
    """
    Enable or disable all notifications at once.
    Corresponds to the "Enable All" and "Disable All" buttons in the UI.
    
    POST /api/notifications/preferences/bulk-action/
    Body: { "action": "enable_all" } or { "action": "disable_all" }
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        try:
            serializer = BulkUpdateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'success': False,
                    'message': 'Invalid action.',
                    'data': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            # Get or create notification preferences
            preferences, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )
            
            # Perform the action
            if action == 'enable_all':
                preferences.enable_all()
                message = 'All notifications have been enabled.'
            elif action == 'disable_all':
                preferences.disable_all()
                message = 'All notifications have been disabled.'
            
            # Return updated preferences
            result_serializer = NotificationPreferenceSerializer(preferences)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': message,
                'data': result_serializer.data
            })
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to perform bulk action.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
