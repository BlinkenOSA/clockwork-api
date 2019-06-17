from django.conf.urls import url
from isaar.views import IsaarSelectList, IsaarList, IsaarDetail

app_name = 'isaar'

urlpatterns = [
    url(r'^$', IsaarList.as_view(), name='isaar-list'),
    url(r'^(?P<pk>[0-9]+)/$', IsaarDetail.as_view(), name='isaar-detail'),
    url(r'^select/$', IsaarSelectList.as_view(), name='isaar-select-list'),
]