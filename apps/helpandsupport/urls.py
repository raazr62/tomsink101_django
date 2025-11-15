from django.urls import path
from .views import (
    HelpAndSupportView,
    ContactSupportView,
    LegalDocumentsListView,
    LegalDocumentDetailView,
    SupportTicketCreateView,
    UserSupportTicketsView,
    SupportTicketDetailView,
)

urlpatterns = [
    # Combined help and support page
    path('helpandsupport/', HelpAndSupportView.as_view(), name='help-support'),
    
    # Contact support
    path('contact/', ContactSupportView.as_view(), name='contact-support'),
    
    # Legal documents
    path('legal/', LegalDocumentsListView.as_view(), name='legal-documents-list'),
    path('legal/<slug:slug>/', LegalDocumentDetailView.as_view(), name='legal-document-detail'),
    
    # Support tickets
    path('ticket/create/', SupportTicketCreateView.as_view(), name='support-ticket-create'),
    path('tickets/', UserSupportTicketsView.as_view(), name='user-support-tickets'),
    path('tickets/<str:ticket_number>/', SupportTicketDetailView.as_view(), name='support-ticket-detail'),
]
