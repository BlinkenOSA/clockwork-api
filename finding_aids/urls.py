from django.urls import path, re_path

from finding_aids.serializers.finding_aids_template_serializers import FindingAidsTemplateListSerializer
from finding_aids.views.finding_aids_grid_views import FindingAidsGridList
from finding_aids.views.finding_aids_template_views import FindingAidsTemplateList, FindingAidsTemplateSelect, \
    FindingAidsTemplateDetail, FindingAidsTemplateCreate, FindingAidsTemplatePreCreate
from finding_aids.views.finding_aids_views import FindingAidsSelectList, FindingAidsCreate, FindingAidsDetail, \
    FindingAidsList, FindingAidsClone, FindingAidsAction, FindingAidsPreCreate, FindingAidsGetNextFolder

app_name = 'finding_aids'

urlpatterns = [
    path('list/<int:container_id>/', FindingAidsList.as_view(), name='finding_aids-list'),
    path('<int:pk>/', FindingAidsDetail.as_view(), name='finding_aids-detail'),
    path('pre_create/<int:container_id>/', FindingAidsPreCreate.as_view(), name='finding_aids-pre-create'),
    path('create/<int:container_id>/', FindingAidsCreate.as_view(), name='finding_aids-create'),
    path('select/<int:container_id>/', FindingAidsSelectList.as_view(), name='finding_aids-select'),

    path('get_next_folder/<int:container_id>/', FindingAidsGetNextFolder.as_view(), name='finding_aids-get-next-folder'),

    path('clone/<int:pk>/', FindingAidsClone.as_view(), name='finding_aids-clone'),

    path('templates/list/<int:series_id>/', FindingAidsTemplateList.as_view(), name='finding_aids-templates-list'),
    path('templates/<int:pk>/', FindingAidsTemplateDetail.as_view(), name='finding_aids-templates-detail'),
    path('templates/pre_create/<int:series_id>/', FindingAidsTemplatePreCreate.as_view(), name='finding_aids-template-pre-create'),
    path('templates/create/<int:series_id>/', FindingAidsTemplateCreate.as_view(), name='finding_aids-templates-create'),
    path('templates/select/<int:series_id>/', FindingAidsTemplateSelect.as_view(), name='finding_aids-templates-list'),

    path('grid/list/<int:series_id>/', FindingAidsGridList.as_view(), name='finding_aids-grid-list'),

    re_path(r'(?P<action>["publish"|"unpublish"|"set_confidential"|"set_non_confidential"]+)/(?P<pk>[0-9]+)/',
            FindingAidsAction.as_view(), name='finding_aids-publish'),
]