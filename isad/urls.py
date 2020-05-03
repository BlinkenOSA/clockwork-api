from django.urls import path, re_path

from isad.views import IsadSelectList, IsadList, IsadDetail, IsadPublish, IsadPreCreate

app_name = 'isad'

urlpatterns = [
    path('', IsadList.as_view(), name='isad-list'),
    path('<int:pk>/', IsadDetail.as_view(), name='isad-detail'),
    path('create/<int:pk>/', IsadPreCreate.as_view(), name='isad-pre-create'),
    path('select/', IsadSelectList.as_view(), name='isad-select-list'),

    re_path(r'(?P<action>["publish"|"unpublish"]+)/(?P<pk>[0-9]+)/$', IsadPublish.as_view(), name='isad-publish'),
]