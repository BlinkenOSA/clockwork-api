"""
URL configuration for the `archival_unit` app.

This module exposes endpoints for:

Hierarchy management
--------------------
    - Listing fonds-level units
    - Retrieving/updating/deleting any archival unit
    - Pre-create metadata for adding child units (F → SF, SF → S)

Selection endpoints
-------------------
    - Lightweight dropdown/select lists
    - Children-by-parent filtered lists (with user access restrictions)

The views work together to support hierarchical navigation through:
Fonds → Subfonds → Series
"""
from django.urls import path

from archival_unit.views import ArchivalUnitSelectList, ArchivalUnitList, ArchivalUnitDetail, ArchivalUnitPreCreate, \
    ArchivalUnitSelectByParentList

app_name = 'archival_unit'

urlpatterns = [
    path('', ArchivalUnitList.as_view(), name='archival_unit-list'),
    path('<int:pk>/', ArchivalUnitDetail.as_view(), name='archival_unit-detail'),
    path('create/<int:pk>/', ArchivalUnitPreCreate.as_view(), name='archival_unit-pre-create'),
    path('select/', ArchivalUnitSelectList.as_view(), name='archival_unit-select-list'),

    path('select/<int:parent_id>/', ArchivalUnitSelectByParentList.as_view(), name='archival_unit-select-by-parent-list'),
]