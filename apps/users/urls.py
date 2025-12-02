from django.urls import path
from .views import (
    SignUpView,
    SignInView,
    SignOutView,
    ChangePasswordView,
    SendOTPView,
    ResendOTPView,
    VerifyOTPView,
    ResetPasswordView,
    UpdateProfileAvatarView,
    UpdateProfileView,
    ProfileGet,
    DeleteAccountView,
    VerifyEmailOTPView,
    ResendVerificationOTPView,
    GoogleLoginView,
    GoogleLoginPageView,
    GoogleCallbackView,
    GoogleTestView,
    dashboard,
)

urlpatterns = [
    
    # Authentication
    path("signup/", SignUpView.as_view(), name="signup"),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('google-login-page/', GoogleLoginPageView.as_view(), name='google-login-page'),
    path('google-callback/', GoogleCallbackView.as_view(), name='google-callback'),
    path('google-test/', GoogleTestView.as_view(), name='google-test'),
    
    # Alternative callback URLs for different Google Console configurations
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google-callback-alt1'),
    path('accounts/google/login/callback/', GoogleCallbackView.as_view(), name='google-callback-alt2'),
    
    path("signin/", SignInView.as_view(), name="signin"),
    path("signout/", SignOutView.as_view(), name="signout"),

    # Email Verification
    path('verify-email-otp/', VerifyEmailOTPView.as_view(), name='verify-email-otp'),
    path('resend-verification-otp/', ResendVerificationOTPView.as_view(), name='resend-verification-otp'),

    # password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # profile
    path('avatar-update/', UpdateProfileAvatarView.as_view(), name='avatar-update'),
    path('profile-update/', UpdateProfileView.as_view(), name='profile-update'),
    path('profile-get/', ProfileGet.as_view(), name='profile-get'),

    # danger zone
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),

    path('dashboard', dashboard, name='dashboard'),
]
