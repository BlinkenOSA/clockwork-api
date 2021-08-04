from django.urls import path

from isaar.views import IsaarSelectList, IsaarList, IsaarDetail, IsaarRelationshipSelectList, \
    IsaarPlaceQualifierSelectList

app_name = 'isaar'

urlpatterns = [
    path('', IsaarList.as_view(), name='isaar-list'),
    path('<int:pk>/', IsaarDetail.as_view(), name='isaar-detail'),
    path('select/', IsaarSelectList.as_view(), name='isaar-select-list'),

    path('relationships/select/', IsaarRelationshipSelectList.as_view(), name='isaar-select-relationship'),
    path('place_qualifiers/select/', IsaarPlaceQualifierSelectList.as_view(), name='isaar-select-place-qualifier'),
]