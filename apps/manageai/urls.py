from django.urls import path
from .views import (
    ChatView,
    ChatSessionListView,
    ChatSessionDetailView,
    ChatSessionCreateView,
)

urlpatterns = [
    # Chat endpoint
    path('chat/', ChatView.as_view(), name='ai-chat'),
    
    # Session management
    path('sessions/', ChatSessionListView.as_view(), name='chat-sessions-list'),
    path('sessions/create/', ChatSessionCreateView.as_view(), name='chat-session-create'),
    path('sessions/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='chat-session-detail'),
]
