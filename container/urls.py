from django.conf.urls import url

from container.views import ContainerList, ContainerDetail, ContainerSelectList, ContainerDetailByBarcode

app_name = 'container'

urlpatterns = [
    url(r'^$', ContainerList.as_view(), name='container-list'),
    url(r'^(?P<pk>[0-9]+)/$', ContainerDetail.as_view(), name='container-detail'),
    url(r'^select/$', ContainerSelectList.as_view(), name='container-select-list'),

    url(r'^(?P<barcode>[HU_OSA[0-9]+)/$', ContainerDetailByBarcode.as_view(), name='container-detail-by-barcode'),
]