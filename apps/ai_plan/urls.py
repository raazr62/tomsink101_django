from django.urls import path
from .views import AIPlanChatView, SessionDetailView


urlpatterns = [
    path("chat/", AIPlanChatView.as_view(), name="ai-plan-chat"),
    path("sessions/", SessionDetailView.as_view(), name="ai-plan-session"),
]
