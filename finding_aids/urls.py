from django.urls import path
from finding_aids.views.finding_aids_views import FindingAidsSelectList, FindingAidsCreate, FindingAidsDetail

app_name = 'finding_aids'

urlpatterns = [
    path('', FindingAidsCreate.as_view(), name='finding_aids-create'),
    path('<int:pk>', FindingAidsDetail.as_view(), name='finding_aids-detail'),
    path('select/<int:container_id>/', FindingAidsSelectList.as_view(), name='finding_aids-select'),
]