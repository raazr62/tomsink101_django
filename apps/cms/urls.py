from django.urls import path
from apps.cms.views import CompleteCMSDataView

app_name = 'cms'

urlpatterns = [
    path('data/', CompleteCMSDataView.as_view(), name='cms-data'),
]
