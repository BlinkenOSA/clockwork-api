from django.urls import path, re_path

from isad.views.isad_index_views import IsadIndexTestView
from isad.views.isad_views import IsadSelectList, IsadList, IsadDetail, IsadPublish, IsadPreCreate, IsadCreate

app_name = 'isad'

urlpatterns = [
    path('', IsadList.as_view(), name='isad-list'),
    path('create/', IsadCreate.as_view(), name='isad-create'),
    path('<int:pk>/', IsadDetail.as_view(), name='isad-detail'),
    path('create/<int:pk>/', IsadPreCreate.as_view(), name='isad-pre-create'),
    path('select/', IsadSelectList.as_view(), name='isad-select-list'),

    re_path(r'index/(?P<target>["ams"|"catalog"]+)/(?P<pk>[0-9]+)/$', IsadIndexTestView.as_view(), name='isad-isad-test-view'),
    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<pk>[0-9]+)/$', IsadPublish.as_view(), name='isad-publish'),
]