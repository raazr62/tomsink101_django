import requests
from django.core.files.base import ContentFile
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User, Profile
from apps.utils.helpers import success,error
from uuid import uuid4
from django.conf import settings

class GoogleAuthView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        access_token = request.data.get('access_token')
        if not access_token:
            return error("Access token is required", code=status.HTTP_400_BAD_REQUEST)

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(
            user_info_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if response.status_code != 200:
            return error("Failed to fetch user info from Google", code=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        email = user_info.get('email')
        name = user_info.get('name')
        given_name = user_info.get('given_name')  
        family_name = user_info.get('family_name')  
        picture = user_info.get('picture') 

        if not email:
            return error("Email not available in Google user info", code=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists, if not create one.
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                password="passworasldfjadslfh@#@32",
                auth_provider='google',
                is_active=True,
                is_email_verified=True
            )
            
            # Create profile
            profile = Profile.objects.create(
                user=user,
                name=f"{given_name} {family_name}" if given_name and family_name else name
            )
            
            # Download and save avatar if available
            if picture:
                try:
                    image_response = requests.get(picture, timeout=10)
                    if image_response.status_code == 200:
                        file_name = f"profile_{uuid4().hex}.jpg"
                        profile.avatar.save(file_name, ContentFile(image_response.content), save=True)
                except Exception as e:
                    # Log error but don't fail the authentication
                    pass
        
        refresh = RefreshToken.for_user(user)
        return success({
            'id': user.id,
            'name': user.profile.name if hasattr(user, 'profile') else '',
            'email': user.email,
            'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None,
            'provider': user.auth_provider,
            'is_google': user.auth_provider == 'google',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        })


class GoogleLoginTestView(APIView):
    """
    Serve the Google login test page
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Check if Google Client ID is configured
        google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        
        if not google_client_id or google_client_id == '':
            # Return setup instructions if not configured
            return render(request, 'socialauth/google_setup.html', {
                'setup_required': True,
                'redirect_uri': request.build_absolute_uri('/api/socialauth/google/callback/')
            })
        
        context = {
            'google_client_id': google_client_id,
            'api_endpoint': request.build_absolute_uri('/api/socialauth/google/'),
        }
        return render(request, 'socialauth/google_login.html', context)