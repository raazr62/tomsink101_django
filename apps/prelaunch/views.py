from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.db.models import Count
from django.db import transaction
from .models import PrelaunchUser, PrelaunchReferral
from apps.users.models import User, Profile, UserReferral
from .helpers import get_client_ip
from .email_templates import send_referral_url_email, send_verification_success_email
from .serializers import (
    PrelaunchUserSerializer,
    PrelaunchUserDetailSerializer,
    PrelaunchReferralSerializer,
    ReferralLeaderboardSerializer,
    PrelaunchStatsSerializer,
)

# Prelaunch Signup
class PrelaunchSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Get IP and user agent for fraud detection
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Prepare data
        data = request.data.copy()
        
        # Priority: body parameter > query parameter
        if not data.get('referred_by'):
            ref_from_query = request.query_params.get('ref')
            if ref_from_query:
                data['referred_by'] = ref_from_query
        
        # Create serializer
        serializer = PrelaunchUserSerializer(data=data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Save the new user
                    user = serializer.save(
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    
                    # If user was referred, create referral record
                    if user.referred_by:
                        if PrelaunchUser.objects.filter(referral_code=user.referred_by).exists():
                            parent_user = PrelaunchUser.objects.get(referral_code=user.referred_by)
                            PrelaunchReferral.objects.create(
                                parent_referral_code=user.referred_by,
                                child_email=user.email,
                                child_user=user,
                                parent_user=parent_user
                            )
                        elif Profile.objects.filter(referral_code=user.referred_by).exists():
                            parent_profile = Profile.objects.get(referral_code=user.referred_by)
                            # For main user referring prelaunch user, create UserReferral
                            UserReferral.objects.create(
                                parent_referral_code=user.referred_by,
                                child_email=user.email,
                                child_profile=None,  # No profile for prelaunch user
                                parent_profile=parent_profile
                            )
                
                # Send referral URL email
                try:
                    send_referral_url_email(user)
                except Exception as e:
                    # Log the error but don't fail the signup
                    print(f"Failed to send referral email: {str(e)}")

                # Send verification success email
                try:
                    send_verification_success_email(user)
                except Exception as e:
                    # Log the error but don't fail the signup
                    print(f"Failed to send verification success email: {str(e)}")
                
                # Return success response
                return Response({
                    'status': status.HTTP_201_CREATED,
                    'success': True,
                    'message': 'Successfully joined the waitlist!',
                    'data': PrelaunchUserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'success': False,
                    'message': 'An error occurred during signup.',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'message': 'Validation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# Prelaunch User Detail
class PrelaunchUserDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PrelaunchUserDetailSerializer

    def get_object(self):
        code = self.request.query_params.get('code')
        email = self.request.query_params.get('email')
        
        if code:
            return PrelaunchUser.objects.get(referral_code=code)
        elif email:
            return PrelaunchUser.objects.get(email=email)
        else:
            raise ValueError("Must provide either 'code' or 'email' parameter")

# Leaderboard
class PrelaunchLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 100)  # Max 100 results
        
        # Get users with referral counts
        users = User.objects.annotate(
            ref_count=Count('referrals_by')
        ).filter(
            ref_count__gt=0
        ).order_by('-ref_count', '-created_at')[:limit]
        
        # Build leaderboard data with rankings
        leaderboard = []
        for rank, user in enumerate(users, start=1):
            leaderboard.append({
                'rank': rank,
                'name': user.name,
                'email': user.email,
                'referral_code': user.referral_code,
                'referral_count': user.ref_count,
                'created_at': user.created_at,
            })
        
        serializer = ReferralLeaderboardSerializer(leaderboard, many=True)
        
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'data': serializer.data
        })

# Overall Statistics
class PrelaunchStatsView(APIView):
    permission_classes = [AllowAny]  # Change to IsAdminUser for admin-only access

    def get(self, request):
        # Calculate statistics
        total_signups = PrelaunchUser.objects.count()
        total_referrals = PrelaunchReferral.objects.count()
        total_activated = PrelaunchUser.objects.filter(activated=True).count()
        
        # Get top 5 referrers
        top_referrers = PrelaunchUser.objects.annotate(
            ref_count=Count('referrals_made')
        ).filter(
            ref_count__gt=0
        ).order_by('-ref_count')[:5]
        
        top_referrers_data = []
        for rank, user in enumerate(top_referrers, start=1):
            top_referrers_data.append({
                'rank': rank,
                'name': user.name,
                'email': user.email,
                'referral_code': user.referral_code,
                'referral_count': user.ref_count,
                'created_at': user.created_at,
            })
        
        # Get 5 most recent signups
        recent_signups = PrelaunchUser.objects.order_by('-created_at')[:5]
        
        # Build response
        stats_data = {
            'total_signups': total_signups,
            'total_referrals': total_referrals,
            'total_activated': total_activated,
            'top_referrers': top_referrers_data,
            'recent_signups': PrelaunchUserSerializer(recent_signups, many=True).data,
        }
        
        serializer = PrelaunchStatsSerializer(stats_data)
        
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'data': serializer.data
        })

# User Referrals
class UserReferralsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        
        if not code:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "success": False,
                "message": "Referral code is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = PrelaunchUser.objects.get(referral_code=code)
            referrals = user.referrals_made.all()
            
            serializer = PrelaunchReferralSerializer(referrals, many=True)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'referral_code': user.referral_code,
                    'referral_count': user.referral_count,
                },
                'referrals': serializer.data
            })
            
        except PrelaunchUser.DoesNotExist:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                "success": False,
                "message": "User not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

# Validate Referral Code
class CheckReferralCodeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        
        if not code:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "success": False,
                "message": "Referral code is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exists = PrelaunchUser.objects.filter(referral_code=code).exists()
        
        if exists:
            user = PrelaunchUser.objects.get(referral_code=code)
            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "valid": True,
                "user": {
                    "name": user.name,
                    "referral_code": user.referral_code,
                }
            })
        else:
            return Response({
                "status": status.HTTP_200_OK,
                "success": True,
                "valid": False,
                "message": "Invalid referral code."
            })

# Check Email Existence
class CheckEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        email = request.query_params.get('email')
        
        if not email:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "success": False,
                "message": "Email is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exists = PrelaunchUser.objects.filter(email=email).exists()
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "exists": exists,
            "message": "Email is already registered." if exists else "Email is available."
        })

# Fraud Detection
class FraudDetectionView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        ip = request.query_params.get('ip')
        email_pattern = request.query_params.get('email')
        
        results = {
            'suspicious_activity': []
        }
        
        if ip:
            # Find users with same IP
            same_ip_users = PrelaunchUser.objects.filter(ip_address=ip)
            if same_ip_users.count() > 1:
                results['suspicious_activity'].append({
                    'type': 'Multiple accounts from same IP',
                    'ip_address': ip,
                    'count': same_ip_users.count(),
                    'users': PrelaunchUserSerializer(same_ip_users, many=True).data
                })
        
        if email_pattern:
            # Find similar email patterns (e.g., test1@gmail.com, test2@gmail.com)
            base_email = email_pattern.split('@')[0] if '@' in email_pattern else email_pattern
            similar_emails = PrelaunchUser.objects.filter(email__icontains=base_email)
            if similar_emails.count() > 1:
                results['suspicious_activity'].append({
                    'type': 'Similar email patterns',
                    'pattern': base_email,
                    'count': similar_emails.count(),
                    'users': PrelaunchUserSerializer(similar_emails, many=True).data
                })
        
        return Response({
            "status": status.HTTP_200_OK,
            "success": True,
            "data": results
        })
