from django.urls import path, re_path
from finding_aids.views.finding_aids_views import FindingAidsSelectList, FindingAidsCreate, FindingAidsDetail, \
    FindingAidsList, FindingAidsClone, FindingAidsAction

app_name = 'finding_aids'

urlpatterns = [
    path('', FindingAidsList.as_view(), name='finding_aids-list'),
    path('<int:pk>/', FindingAidsDetail.as_view(), name='finding_aids-detail'),
    path('create/<int:container_id>/', FindingAidsCreate.as_view(), name='finding_aids-create'),
    path('select/<int:container_id>/', FindingAidsSelectList.as_view(), name='finding_aids-select'),

    path('clone/<int:pk>/', FindingAidsClone.as_view(), name='finding_aids-clone'),

    re_path(r'(?P<action>["publish"|"unpublish"|"set_confidential"|"set_non_confidential"]+)/(?P<pk>[0-9]+)/$',
            FindingAidsAction.as_view(), name='finding_aids-publish'),
]