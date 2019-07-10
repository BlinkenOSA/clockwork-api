from django.urls import path, re_path
from finding_aids.views.finding_aids_views import FindingAidsSelectList, FindingAidsCreate, FindingAidsDetail, \
    FindingAidsPublish

app_name = 'finding_aids'

urlpatterns = [
    path('<int:pk>', FindingAidsDetail.as_view(), name='finding_aids-detail'),
    path('create/<int:container_id>/', FindingAidsCreate.as_view(), name='finding_aids-create'),
    path('select/<int:container_id>/', FindingAidsSelectList.as_view(), name='finding_aids-select'),

    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<pk>[0-9]+)/$',
            FindingAidsPublish.as_view(), name='finding_aids-publish'),
]