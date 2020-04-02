from django.urls import path

from archival_unit.views import ArchivalUnitSelectList, ArchivalUnitList, ArchivalUnitDetail

app_name = 'archival_unit'

urlpatterns = [
    path('', ArchivalUnitList.as_view(), name='archival_unit-list'),
    path('<int:pk>/', ArchivalUnitDetail.as_view(), name='archival_unit-detail'),
    path('select/', ArchivalUnitSelectList.as_view(), name='archival_unit-select-list'),
]