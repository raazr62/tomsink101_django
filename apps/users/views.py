from .models import User, Profile
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.urls import reverse_lazy
from django.db.models import Count
import json
from django.db.models.functions import TruncDate
from rest_framework.validators import ValidationError
from django.utils import timezone
from .serializers import (
    SignUpSerializer,
    SignInSerializer,
    SignOutSerializer,
    ChangePasswordSerializer,
    SendOTPSerializer,
    ResendOTPSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    UpdateProfileAvatarSerializer,
    UserProfileSerializer,
    DeleteAccountSerializer,
    VerifyEmailOTPSerializer,
    ResendVerificationOTPSerializer,
)
from django.http import Http404
from apps.utils.helpers import success, error


# Create your views here.
class SignUpView(APIView):
    permission_classes = []

    def post(self, request):

        serializer = SignUpSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success(data=serializer.data,message="User created successfully. Please check your email to verify your account.",code=status.HTTP_201_CREATED, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

class SignInView(APIView):

    permission_classes = []

    def post(self, request):
        
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            return success(data=serializer.data, message="Signin successful.", code=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)


class SignOutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = SignOutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'Logout successful.', 'data': serializer.data}, status.HTTP_200_OK)
        return Response({'status':status.HTTP_400_BAD_REQUEST, 'success':False, 'message': 'Logout failed.', 'data': serializer.errors}, status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'Password change successfully.', 'data': []}, status.HTTP_200_OK)
        raise ValidationError(serializer.errors)

class SendOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'OTP send to mail successfully.', 'data': []}, status.HTTP_200_OK)
        errors = serializer.errors
        if "email" in errors:
            errors["error"] = errors.pop("email")
        raise ValidationError(errors)

class ResendOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'OTP send to mail successfully.', 'data': []}, status.HTTP_200_OK)
        errors = serializer.errors
        if "email" in errors:
            errors["error"] = errors.pop("email")
        raise ValidationError(errors)

class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'OTP verify is successfully.', 'data': []}, status.HTTP_200_OK)
        return Response({'status':status.HTTP_400_BAD_REQUEST, 'success':False, 'message': 'OTP verify is failed.', 'data': serializer.errors}, status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'Password reset successfully.', 'data': []}, status.HTTP_200_OK)
        errors = serializer.errors
        if "non_field_errors" in errors:
            errors["error"] = errors.pop("non_field_errors")
        return Response({'status':status.HTTP_400_BAD_REQUEST, 'success':False, 'message': 'Password reset failed.', 'data': errors}, status.HTTP_400_BAD_REQUEST)



class UpdateProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request):
        user = request.user

        try:
            profile = Profile.objects.select_related('user').get(user=user)
        except Profile.DoesNotExist as e:
            return Response({'status': status.HTTP_400_BAD_REQUEST, 'success': 'false', 'message': 'User not Found.', 'data': str(e)}, status.HTTP_400_BAD_REQUEST)

        serializer = UpdateProfileAvatarSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_200_OK, 'success':True, 'message': 'Profile avatar update successfully.', 'data': serializer.data}, status.HTTP_200_OK)
        return Response({'status':status.HTTP_400_BAD_REQUEST, 'success':False, 'message': 'Profile avatar update failed.', 'data': serializer.errors}, status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request):
        user = request.user

        try:
            profile = Profile.objects.select_related('user').get(user=user)
        except Profile.DoesNotExist:
            return Response({'status': status.HTTP_400_BAD_REQUEST, 'success': False, 'message': 'User not found.', 'data': []})

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': status.HTTP_200_OK, 'success': True, 'message': 'Profile update successfully.', 'data': serializer.data})
        return Response({'status': status.HTTP_400_BAD_REQUEST, 'success': False, 'message': 'Profile update failed.', 'data': serializer.errors})


class ProfileGet(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user

        try:
            profile = Profile.objects.select_related('user').get(user=user)
        except Profile.DoesNotExist:
            return Response({'status': status.HTTP_400_BAD_REQUEST, 'success': False, 'message': 'User not found.', 'data': []})

        data = {
            'id': profile.id,
            'email': profile.user.email,
            'name': profile.name,
            'accepted_terms': profile.accepted_terms,
            'avatar_url': profile.avatar.url if profile.avatar else None,
            'created_at': profile.created_at,
            'updated_at': profile.updated_at,
        }
        return Response({'status': status.HTTP_200_OK, 'success': True, 'message': 'Profile get successfully.', 'data': data})


class DeleteAccountView(APIView):
    """
    Delete Account View - Permanently deletes the authenticated user's account.
    Requires password confirmation and explicit confirmation flag.
    This action is irreversible and will cascade delete all related data.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            deleted_email = serializer.save()
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Your account has been permanently deleted. We\'re sorry to see you go.',
                'data': {
                    'deleted_email': deleted_email,
                    'deleted_at': timezone.now()
                }
            })
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'message': 'Account deletion failed.',
            'data': serializer.errors
        })


class VerifyEmailOTPView(APIView):
    """
    API View for verifying email address using OTP
    POST: Verify email using OTP sent to email
    """
    permission_classes = []

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Email verified successfully! You can now sign in.',
                'data': {
                    'email': user.email,
                    'is_email_verified': user.is_email_verified
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'message': 'Email verification failed.',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationOTPView(APIView):
    """
    API View for resending verification OTP
    POST: Resend verification OTP to user's email
    """
    permission_classes = []

    def post(self, request):
        serializer = ResendVerificationOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Verification OTP sent successfully. Please check your inbox.',
                'data': {
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'message': 'Failed to resend verification OTP.',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
from django.shortcuts import render
from rest_framework.views import APIView
from apps.users.serializers import GoogleSerializer
from rest_framework.response import Response
from rest_framework import status
from apps.users.utils import register_with_google
# Create your views here.

class GoogleLoginView(APIView):
    def post(self,request):
        serializer = GoogleSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = (serializer.validated_data)['access_token']
            return Response({
                'status':status.HTTP_200_OK,
                'success':True,
                'message':'Login successful.',
                'data':data
            },status=status.HTTP_200_OK)
        return Response({
            'status':status.HTTP_400_BAD_REQUEST,
            'success':False,
            'message':'Login failed.',
            'data':serializer.errors
        },status=status.HTTP_400_BAD_REQUEST)
        
        
from django.shortcuts import render
from django.views import View
from django.conf import settings

class LoginPage(View):
    def get(self, request):
        return render(request, 'login.html',{
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'callback_url': settings.GOOGLE_OAUTH_CALLBACK_URL
        })

