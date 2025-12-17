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
    path('signup/', PrelaunchSignupView.as_view(), name='prelaunch-signup'),
    path('user/', PrelaunchUserDetailView.as_view(), name='prelaunch-user-detail'),
    path('leaderboard/', PrelaunchLeaderboardView.as_view(), name='prelaunch-leaderboard'),
    path('stats/', PrelaunchStatsView.as_view(), name='prelaunch-stats'),
    path('referrals/', UserReferralsView.as_view(), name='user-referrals'),
    path('check-code/', CheckReferralCodeView.as_view(), name='check-referral-code'),
    path('check-email/', CheckEmailView.as_view(), name='check-email'),
    path('fraud-detection/', FraudDetectionView.as_view(), name='fraud-detection'),
]
