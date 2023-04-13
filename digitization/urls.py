from django.urls import path

from digitization.views import DigitizationList, DigitizationDetail

app_name = 'digitization'

urlpatterns = [
    path('container/', DigitizationList.as_view(), name='digitization-list'),
    path('container/<int:pk>/', DigitizationDetail.as_view(), name='digitization-detail'),
]