from django.urls import path
from .views import (
    PrelaunchSignupView,
    PrelaunchUserDetailView,
    PrelaunchLeaderboardView,
    PrelaunchStatsView,
    UserReferralsView,
    CheckReferralCodeView,
    CheckEmailView,
    FraudDetectionView,
)

urlpatterns = [
    # User signup endpoint
    path('signup/', PrelaunchSignupView.as_view(), name='prelaunch-signup'),
    
    # Get user details by referral code or email
    path('user/', PrelaunchUserDetailView.as_view(), name='prelaunch-user-detail'),
    
    # Leaderboard - top referrers
    path('leaderboard/', PrelaunchLeaderboardView.as_view(), name='prelaunch-leaderboard'),
    
    # Overall statistics
    path('stats/', PrelaunchStatsView.as_view(), name='prelaunch-stats'),
    
    # Get all referrals made by a user
    path('referrals/', UserReferralsView.as_view(), name='user-referrals'),
    
    # Validate referral code
    path('check-code/', CheckReferralCodeView.as_view(), name='check-referral-code'),
    
    # Check if email exists
    path('check-email/', CheckEmailView.as_view(), name='check-email'),
    
    # Fraud detection (admin only)
    path('fraud-detection/', FraudDetectionView.as_view(), name='fraud-detection'),
]
