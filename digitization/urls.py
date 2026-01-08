"""
URL configuration for digitization workflows.

These routes provide read-only endpoints used by the Digitization module of the
Archival Management System components to:
    - browse digitized containers
    - inspect container-level technical metadata
    - browse digitized finding-aid entities
    - inspect finding-aid-level technical metadata
"""

from django.urls import path

from digitization.views.container_views import DigitizationContainerDetail, DigitizationContainerList
from digitization.views.finding_aids_views import DigitizationFindingAidsList, DigitizationFindingAidsDetail

app_name = 'digitization'

urlpatterns = [
    # Container digitization endpoints
    path('container/', DigitizationContainerList.as_view(), name='digitization-list'),
    path('container/<int:pk>/', DigitizationContainerDetail.as_view(), name='digitization-detail'),

    # Finding aids digitization endpoints
    path('finding_aids/', DigitizationFindingAidsList.as_view(), name='digitization-finding_aids-list'),
    path('finding_aids/<int:pk>/', DigitizationFindingAidsDetail.as_view(), name='digitization-finding_aids-detail'),
]
