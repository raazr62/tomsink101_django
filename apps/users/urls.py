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
    LoginPage,
)

urlpatterns = [
    
    # Authentication
    path("signup/", SignUpView.as_view(), name="signup"),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
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
    
    path('login1/', LoginPage.as_view(), name='login1'),

]
