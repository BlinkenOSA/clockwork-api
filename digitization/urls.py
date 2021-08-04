from django.urls import path

from digitization.views import DigitizationList, DigitizationDetail

app_name = 'digitization'

urlpatterns = [
    path('', DigitizationList.as_view(), name='digitization-list'),
    path('<int:pk>/', DigitizationDetail.as_view(), name='digitization-detail'),
]