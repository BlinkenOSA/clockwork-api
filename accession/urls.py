from django.conf.urls import url

from accession.views.accession_views import AccessionList, AccessionDetail, AccessionSelectList
from accession.views.select_views import AccessionMethodSelectList, AccessionCopyrightStatusSelectList


app_name = 'accession'

urlpatterns = [
    url(r'^$', AccessionList.as_view(), name='accession-list'),
    url(r'^(?P<pk>[0-9]+)/$', AccessionDetail.as_view(), name='accession-detail'),
    url(r'^select/$', AccessionSelectList.as_view(), name='accession-select-list'),

    # Select URLs
    url(r'^select/accession_copyright_status/$', AccessionCopyrightStatusSelectList.as_view(),
        name='accession_copyright_status-select-list'),
    url(r'^select/accession_methods/$', AccessionMethodSelectList.as_view(), name='accession_method-select-list'),
]