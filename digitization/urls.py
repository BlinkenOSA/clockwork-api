from django.urls import path

from digitization.views.container_views import DigitizationContainerDetail, DigitizationContainerList
from digitization.views.finding_aids_views import DigitizationFindingAidsList, DigitizationFindingAidsDetail

app_name = 'digitization'

urlpatterns = [
    path('container/', DigitizationContainerList.as_view(), name='digitization-list'),
    path('container/<int:pk>/', DigitizationContainerDetail.as_view(), name='digitization-detail'),

    path('finding_aids/', DigitizationFindingAidsList.as_view(), name='digitization-finding_aids-list'),
    path('finding_aids/<int:pk>/', DigitizationFindingAidsDetail.as_view(), name='digitization-finding_aids-detail'),
]
