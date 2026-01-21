"""
finding_aids URL configuration.

This module defines the REST endpoints for managing Finding Aids entities and
related workflows, including:

Entity CRUD and helpers:
    - list entities within a container
    - pre-create payload (numbering + reference code)
    - create/update/delete entities
    - selection list for UI widgets
    - compute the next folder/sequence numbers
    - clone entities
    - state actions (publish/unpublish/confidential)

Templates:
    - list/select templates per series
    - pre-create payload for templates
    - create/update/delete templates

Grid / XLSX workflows:
    - list records for an Excel-like grid UI
    - export grid data as XLSX

Indexing:
    - testing endpoints for indexing to Solr (AMS/Catalog targets)

Label printing:
    - generate container label PDFs (via Jasper templates)
    - carrier type breakdown for label printing UI

Excel export:
    - full excel export endpoint (series-level)
"""

from django.urls import path, re_path

from finding_aids.views.finding_aids_excel_views import FindingAidsExcelExport
from finding_aids.views.finding_aids_grid_views import FindingAidsGridList, FindingAidsGridListExport
from finding_aids.views.finding_aids_index_views import FindingAidsEntityIndexTestView
from finding_aids.views.finding_aids_label_views import FindingAidsLabelDataView, FindingAidsCarrierTypeDataView
from finding_aids.views.finding_aids_template_views import FindingAidsTemplateList, FindingAidsTemplateSelect, \
    FindingAidsTemplateDetail, FindingAidsTemplateCreate, FindingAidsTemplatePreCreate
from finding_aids.views.finding_aids_views import FindingAidsSelectList, FindingAidsCreate, FindingAidsDetail, \
    FindingAidsList, FindingAidsClone, FindingAidsAction, FindingAidsPreCreate, FindingAidsGetNextFolder

app_name = 'finding_aids'

urlpatterns = [
    # Finding Aids entities (container-scoped)
    path('list/<int:container_id>/', FindingAidsList.as_view(), name='finding_aids-list'),
    path('<int:pk>/', FindingAidsDetail.as_view(), name='finding_aids-detail'),
    path('pre_create/<int:container_id>/', FindingAidsPreCreate.as_view(), name='finding_aids-pre-create'),
    path('create/<int:container_id>/', FindingAidsCreate.as_view(), name='finding_aids-create'),
    path('select/<int:container_id>/', FindingAidsSelectList.as_view(), name='finding_aids-select'),

    path('get_next_folder/<int:container_id>/', FindingAidsGetNextFolder.as_view(), name='finding_aids-get-next-folder'),

    path('clone/<int:pk>/', FindingAidsClone.as_view(), name='finding_aids-clone'),

    # Templates (series-scoped)
    path('templates/list/<int:series_id>/', FindingAidsTemplateList.as_view(), name='finding_aids-templates-list'),
    path('templates/<int:pk>/', FindingAidsTemplateDetail.as_view(), name='finding_aids-templates-detail'),
    path('templates/pre_create/<int:series_id>/', FindingAidsTemplatePreCreate.as_view(), name='finding_aids-template-pre-create'),
    path('templates/create/<int:series_id>/', FindingAidsTemplateCreate.as_view(), name='finding_aids-templates-create'),
    path('templates/select/<int:series_id>/', FindingAidsTemplateSelect.as_view(), name='finding_aids-templates-list'),

    # Grid (series-scoped) + XLSX export for spreadsheet-like workflows
    path('grid/list/<int:series_id>/', FindingAidsGridList.as_view(), name='finding_aids-grid-list'),
    path('grid/list/export/<int:series_id>/', FindingAidsGridListExport.as_view(), name='finding_aids-grid-list-export'),

    # Indexing test (targets: "ams" | "catalog")
    re_path(r'index/(?P<target>["ams"|"catalog"]+)/(?P<pk>[0-9]+)/$', FindingAidsEntityIndexTestView.as_view(),
            name='finding-aids-index-test-view'),

    # Label printing (series-scoped)
    path('labels/<int:carrier_type_id>/<int:series_id>/', FindingAidsLabelDataView.as_view(),
         name='finding_aids_label_data_view'),

    # Carrier Type data
    path('carriers/<int:series_id>/', FindingAidsCarrierTypeDataView.as_view(),
         name='finding_aids_carrier_type_data_view'),

    # Excel export (series-scoped)
    path('excel/export/<int:series_id>/', FindingAidsExcelExport.as_view(), name='finding_aids-excel-export'),

    # Actions (publish/unpublish/confidential toggles)
    re_path(r'(?P<action>["publish"|"unpublish"|"set_confidential"|"set_non_confidential"]+)/(?P<pk>[0-9]+)/',
            FindingAidsAction.as_view(), name='finding_aids-publish')
]