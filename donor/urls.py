from django.conf.urls import url

from donor.views import DonorList, DonorDetail, DonorSelectList

app_name = 'donor'

urlpatterns = [
    # Donor URLs
    url(r'^$', DonorList.as_view(), name='donor-list'),
    url(r'^(?P<pk>[0-9]+)/$', DonorDetail.as_view(), name='donor-detail'),
    url(r'^select/$', DonorSelectList.as_view(), name='donor-select-list'),
]