from django.urls import path
from .views import (
    NotificationPreferenceView,
    NotificationPreferenceUpdateView,
    NotificationBulkActionView,
)

urlpatterns = [
    # Get notification preferences
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    
    # Update notification preferences
    path('preferences/update/', NotificationPreferenceUpdateView.as_view(), name='notification-preferences-update'),
    
    # Bulk actions (Enable All / Disable All)
    path('preferences/bulk-action/', NotificationBulkActionView.as_view(), name='notification-bulk-action'),
]
