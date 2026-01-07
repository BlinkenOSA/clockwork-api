"""
URL configuration for container-related API endpoints.

These routes expose read, create, publish, and lookup operations for
containers within an archival series. Endpoints support both identifier-
based and barcode-based access patterns.
"""

from django.urls import re_path, path

from container.views import ContainerList, ContainerDetail, ContainerDetailByBarcode, \
    ContainerCreate, ContainerPreCreate, ContainerPublish, ContainerPublishAll

app_name = 'container'

urlpatterns = [
    # List containers belonging to a specific archival series
    path('list/<int:series_id>/', ContainerList.as_view(), name='container-list'),

    # Prepare container creation with derived defaults
    path('precreate/<int:pk>/', ContainerPreCreate.as_view(), name='container-pre-create'),

    # Create a new container
    path('create/', ContainerCreate.as_view(), name='container-create'),

    # Retrieve or update a container by primary key
    path('<int:pk>/', ContainerDetail.as_view(), name='container-detail'),

    # Publish or unpublish all containers in a series
    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<series>[0-9]+)/all/$',
            ContainerPublishAll.as_view(), name='container-publish-all'),

    # Publish or unpublish a single container
    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<pk>[0-9]+)/$',
            ContainerPublish.as_view(), name='container-publish'),

    # Retrieve a container using its physical barcode identifier
    re_path(r'^(?P<barcode>[HU_OSA[0-9]+)/$', ContainerDetailByBarcode.as_view(), name='container-detail-by-barcode'),
]