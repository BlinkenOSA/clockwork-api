from django.urls.conf import path

from research.views.researcher_views import ResearcherList, ResearcherDetail, ResearcherSelectList, \
    ResearcherCountrySelectList, ResearcherNationalitySelectList
from research.views.researher_degree_views import ResearcherDegreeList, ResearcherDegreeDetail, \
    ResearcherDegreeSelectList

app_name = 'research'

urlpatterns = [
    path('', ResearcherList.as_view(), name='researcher-list'),
    path('<int:pk>/', ResearcherDetail.as_view(), name='researher-detail'),
    path('select/', ResearcherSelectList.as_view(), name='researcher-select-list'),

    path('degree', ResearcherDegreeList.as_view(), name='researcher-degree-list'),
    path('degree/<int:pk>/', ResearcherDegreeDetail.as_view(), name='researher-degree-detail'),
    path('degree/select/', ResearcherDegreeSelectList.as_view(), name='researcher-degree-select-list'),

    path('country/select/', ResearcherCountrySelectList.as_view(), name='researcher-country-select-list'),
    path('nationality/select/', ResearcherNationalitySelectList.as_view(), name='researcher-nationality-select-list'),
]