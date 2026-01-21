"""
URL configuration for donor management.

These routes provide CRUD and selection endpoints for donor records,
supporting both individual and corporate donors.
"""

from django.urls import path

from donor.views import DonorList, DonorDetail, DonorSelectList

app_name = 'donor'

urlpatterns = [
    # Donor list and creation
    path('', DonorList.as_view(), name='donor-list'),

    # Donor detail, update, and deletion
    path('<int:pk>/', DonorDetail.as_view(), name='donor-detail'),

    # Donor selection endpoint
    path('select/', DonorSelectList.as_view(), name='donor-select-list'),
]