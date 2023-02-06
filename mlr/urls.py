from django.urls import path

from mlr.views import *

app_name = 'mlr'

urlpatterns = [
    path('', MLRList.as_view(), name='mlr-list'),
    path('<int:pk>/', MLRDetail.as_view(), name='mlr-detail'),
    path('exportcsv/', MLRExportCSV.as_view(), name='mlr-export-csv'),
]

