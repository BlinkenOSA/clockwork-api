from django.urls import path

from donor.views import DonorList, DonorDetail, DonorSelectList

app_name = 'donor'

urlpatterns = [
    path('', DonorList.as_view(), name='donor-list'),
    path('<int:pk>/', DonorDetail.as_view(), name='donor-detail'),
    path('select/', DonorSelectList.as_view(), name='donor-select-list'),
]