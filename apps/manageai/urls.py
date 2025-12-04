from django.urls import path
from .views import (
    ChatView,
    ChatSessionListView,
    ChatSessionDetailView,
    ChatSessionCreateView,
    ChatSessionPlansView,
    ModifyPlanView,
    LastChatSessionView,
)

urlpatterns = [
    # Chat endpoint
    path('chat/', ChatView.as_view(), name='ai-chat'),
    
    # Plan modification endpoint
    path('modify-plan/', ModifyPlanView.as_view(), name='modify-plan'),
    
    # Session management
    path('sessions/', ChatSessionListView.as_view(), name='chat-sessions-list'),
    path('sessions/create/', ChatSessionCreateView.as_view(), name='chat-session-create'),
    path('sessions/last/', LastChatSessionView.as_view(), name='last-chat-session'),
    path('sessions/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='chat-session-detail'),
    path('sessions/<uuid:session_id>/plans/', ChatSessionPlansView.as_view(), name='chat-session-plans'),
]
