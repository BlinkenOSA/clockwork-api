from django.urls import re_path, path

from container.views import ContainerList, ContainerDetail, ContainerDetailByBarcode, \
    ContainerCreate, ContainerPreCreate, ContainerPublish, ContainerPublishAll

app_name = 'container'

urlpatterns = [
    path('list/<int:series_id>/', ContainerList.as_view(), name='container-list'),
    path('precreate/<int:pk>/', ContainerPreCreate.as_view(), name='container-pre-create'),
    path('create/', ContainerCreate.as_view(), name='container-create'),
    path('<int:pk>/', ContainerDetail.as_view(), name='container-detail'),

    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<series>[0-9]+)/all/$',
            ContainerPublishAll.as_view(), name='container-publish-all'),
    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<pk>[0-9]+)/$',
            ContainerPublish.as_view(), name='container-publish'),

    re_path(r'^(?P<barcode>[HU_OSA[0-9]+)/$', ContainerDetailByBarcode.as_view(), name='container-detail-by-barcode'),
]