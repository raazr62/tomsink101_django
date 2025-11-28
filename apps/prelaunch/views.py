from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.db.models import Count, Q
from django.db import transaction
from .models import PrelaunchUser, PrelaunchReferral
from .serializers import (
    PrelaunchUserSerializer,
    PrelaunchUserDetailSerializer,
    PrelaunchReferralSerializer,
    ReferralLeaderboardSerializer,
    PrelaunchStatsSerializer,
)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class PrelaunchSignupView(APIView):
    """
    POST endpoint for users to join the waitlist.
    
    Required fields:
    - name: User's full name
    - email: User's email address
    
    Optional fields:
    - referred_by: Referral code of the person who invited them (can be in body or query param 'ref')
    
    Query params:
    - ref: Referral code (alternative to 'referred_by' in body)
    
    Response includes:
    - User details
    - Unique referral code
    - Referral link to share
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get IP and user agent for fraud detection
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Prepare data
        data = request.data.copy()
        
        # Check for referral code in query params (e.g., ?ref=john-abc123)
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
                        try:
                            parent_user = PrelaunchUser.objects.get(referral_code=user.referred_by)
                            PrelaunchReferral.objects.create(
                                parent_referral_code=user.referred_by,
                                child_email=user.email,
                                child_user=user,
                                parent_user=parent_user
                            )
                        except PrelaunchUser.DoesNotExist:
                            pass  # Already validated in serializer
                
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


class PrelaunchUserDetailView(generics.RetrieveAPIView):
    """
    GET endpoint to retrieve user details by referral code or email.
    
    Query params:
    - code: Referral code
    - email: Email address
    """
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


class PrelaunchLeaderboardView(APIView):
    """
    GET endpoint to retrieve referral leaderboard.
    Shows top users by referral count.
    
    Query params:
    - limit: Number of results (default: 10, max: 100)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 100)  # Max 100 results
        
        # Get users with referral counts
        users = PrelaunchUser.objects.annotate(
            ref_count=Count('referrals_made')
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


class PrelaunchStatsView(APIView):
    """
    GET endpoint for overall pre-launch statistics.
    
    Returns:
    - Total signups
    - Total referrals
    - Total activated users
    - Top 5 referrers
    - 5 most recent signups
    """
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


class UserReferralsView(APIView):
    """
    GET endpoint to retrieve all referrals made by a specific user.
    
    Query params:
    - code: Referral code of the user
    """
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


class CheckReferralCodeView(APIView):
    """
    GET endpoint to validate a referral code.
    
    Query params:
    - code: Referral code to validate
    """
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


class CheckEmailView(APIView):
    """
    GET endpoint to check if an email is already registered.
    
    Query params:
    - email: Email address to check
    """
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


class FraudDetectionView(APIView):
    """
    GET endpoint to detect potential fraud based on IP address or email patterns.
    Admin only.
    
    Query params:
    - ip: IP address to check
    - email: Email to check for duplicates
    """
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
