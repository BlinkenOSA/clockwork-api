from django.urls import re_path, path

from container.views import ContainerList, ContainerDetail, ContainerSelectList, ContainerDetailByBarcode

app_name = 'container'

urlpatterns = [
    path('', ContainerList.as_view(), name='container-list'),
    path('<int:pk>/', ContainerDetail.as_view(), name='container-detail'),
    path('select/', ContainerSelectList.as_view(), name='container-select-list'),

    re_path(r'^(?P<barcode>[HU_OSA[0-9]+)/$', ContainerDetailByBarcode.as_view(), name='container-detail-by-barcode'),
]