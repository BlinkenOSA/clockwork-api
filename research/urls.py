from django.urls.conf import path, re_path

from research.views.researcher_views import ResearcherList, ResearcherDetail, ResearcherSelectList, \
    ResearcherCountrySelectList, ResearcherNationalitySelectList, ResearcherActivate, ResearcherApprove, \
    ResearcherCountryActiveSelectList, ResearcherNationalityActiveSelectList
from research.views.researcher_visit_views import ResearcherVisitsList, ResearcherVisitsCheckOut, \
    ResearcherVisitsCheckIn
from research.views.researcher_degree_views import ResearcherDegreeList, ResearcherDegreeDetail, \
    ResearcherDegreeSelectList

app_name = 'research'

urlpatterns = [
    path('researcher', ResearcherList.as_view(), name='researcher-list'),
    path('researcher/<int:pk>/', ResearcherDetail.as_view(), name='researher-detail'),
    path('researcher/select/', ResearcherSelectList.as_view(), name='researcher-select-list'),

    path('degree', ResearcherDegreeList.as_view(), name='researcher-degree-list'),
    path('degree/<int:pk>/', ResearcherDegreeDetail.as_view(), name='researher-degree-detail'),
    path('degree/select/', ResearcherDegreeSelectList.as_view(), name='researcher-degree-select-list'),

    path('visits', ResearcherVisitsList.as_view(), name='researcher-visits-list'),
    path('visits/check-in/<int:researcher_id>', ResearcherVisitsCheckIn.as_view(), name='researcher-visits-check-in'),
    path('visits/check-out/<int:pk>', ResearcherVisitsCheckOut.as_view(), name='researcher-visits-check-out'),

    path('country/select/', ResearcherCountrySelectList.as_view(), name='researcher-country-select-list'),
    path('nationality/select/', ResearcherNationalitySelectList.as_view(), name='researcher-nationality-select-list'),

    re_path(r'researcher/(?P<action>["activate"|"deactivate"]+)/(?P<pk>[0-9]+)/$', ResearcherActivate.as_view(),
            name='researcher-activate'),
    re_path(r'researcher/(?P<action>["approve"|"disapprove"]+)/(?P<pk>[0-9]+)/$', ResearcherApprove.as_view(),
            name='researcher-approve'),

    path('researcher/country-used/select/', ResearcherCountryActiveSelectList.as_view(),
         name='researcher-country-active-select-list'),
    path('researcher/nationality-used/select/', ResearcherNationalityActiveSelectList.as_view(),
         name='researcher-nationality-active-select-list'),
]