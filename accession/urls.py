"""
URL configuration for the accession app.

This module defines all HTTP endpoints related to accession records,
including:
    - Listing and creating accessions
    - Retrieving, updating, or deleting a specific accession
    - Pre-create utilities (sequence number generation)
    - Lightweight selection endpoints for dropdown fields
    - Controlled vocabulary selection endpoints (methods, copyright statuses)

The structure is organized so that:
    - Main CRUD endpoints remain at the root level
    - Selection lists live under `/select/`
"""
from django.urls import path

from accession.views.accession_views import AccessionList, AccessionDetail, AccessionSelectList, AccessionPreCreate
from accession.views.select_views import AccessionMethodSelectList, AccessionCopyrightStatusSelectList


app_name = 'accession'

urlpatterns = [
    path('', AccessionList.as_view(), name='accession-list'),
    path('<int:pk>/', AccessionDetail.as_view(), name='accession-detail'),
    path('create/', AccessionPreCreate.as_view(), name='accession-pre-create'),
    path('select/', AccessionSelectList.as_view(), name='accession-select-list'),

    # Select URLs
    path('select/accession_copyright_status/', AccessionCopyrightStatusSelectList.as_view(),
         name='accession_copyright_status-select-list'),
    path('select/accession_method/', AccessionMethodSelectList.as_view(),
         name='accession_method-select-list'),
]