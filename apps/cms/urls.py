from django.urls import path
from apps.cms.views import CompleteCMSDataView, HelpSupportView, LegalDocumentView

app_name = 'cms'

urlpatterns = [
    path('data/', CompleteCMSDataView.as_view(), name='cms-data'),
    path('help-support/', HelpSupportView.as_view(), name='help-support'),
    path('legal-documents/<str:doc_type>/', LegalDocumentView.as_view(), name='legal-documents'),
]
