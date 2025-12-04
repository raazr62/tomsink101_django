from django.urls import path
from .views import GoogleAuthView, GoogleLoginTestView

urlpatterns = [
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
    path('google/test/', GoogleLoginTestView.as_view(), name='google-login-test'),
]