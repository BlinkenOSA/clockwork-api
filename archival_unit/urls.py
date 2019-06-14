from django.conf.urls import url

from archival_unit.views import ArchivalUnitSelectList, ArchivalUnitList, ArchivalUnitDetail

app_name = 'archival_unit'

urlpatterns = [
    url(r'^$', ArchivalUnitList.as_view(), name='archival_unit-list'),
    url(r'^(?P<pk>[0-9]+)/$', ArchivalUnitDetail.as_view(), name='archival_unit-detail'),
    url(r'^select/$', ArchivalUnitSelectList.as_view(), name='archival_unit-select-list'),
]