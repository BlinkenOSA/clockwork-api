from django.conf.urls import url

from authority.views.corporation_views import CorporationList, CorporationDetail, CorporationSelectList
from authority.views.country_views import CountryList, CountryDetail, CountrySelectList
from authority.views.genre_views import GenreList, GenreDetail, GenreSelectList
from authority.views.language_views import LanguageList, LanguageDetail, LanguageSelectList
from authority.views.person_views import PersonList, PersonDetail, PersonSelectList
from authority.views.place_views import PlaceList, PlaceDetail, PlaceSelectList
from authority.views.lcsh_views import LCSHList
from authority.views.subject_views import SubjectList, SubjectDetail, SubjectSelectList
from authority.views.viaf_views import VIAFList
from authority.views.wikipedia_views import WikipediaList

app_name = 'authority'

urlpatterns = [
    # Country URLs
    url(r'^countries/$', CountryList.as_view(), name='country-list'),
    url(r'^countries/(?P<pk>[0-9]+)/$', CountryDetail.as_view(), name='country-detail'),
    url(r'^select/countries/$', CountrySelectList.as_view(), name='country-select-list'),

    # Language URLs
    url(r'^languages/$', LanguageList.as_view(), name='language-list'),
    url(r'^languages/(?P<pk>[0-9]+)/$', LanguageDetail.as_view(), name='language-detail'),
    url(r'^select/languages/$', LanguageSelectList.as_view(), name='language-select-list'),

    # Place URLs
    url(r'^places/$', PlaceList.as_view(), name='place-list'),
    url(r'^places/(?P<pk>[0-9]+)/$', PlaceDetail.as_view(), name='place-detail'),
    url(r'^select/places/$', PlaceSelectList.as_view(), name='place-select-list'),

    # Person URLs
    url(r'^people/$', PersonList.as_view(), name='person-list'),
    url(r'^people/(?P<pk>[0-9]+)/$', PersonDetail.as_view(), name='person-detail'),
    url(r'^select/people/$', PersonSelectList.as_view(), name='person-select-list'),

    # Corporation URLs
    url(r'^corporations/$', CorporationList.as_view(), name='corporation-list'),
    url(r'^corporations/(?P<pk>[0-9]+)/$', CorporationDetail.as_view(), name='corporation-detail'),
    url(r'^select/corporations/$', CorporationSelectList.as_view(), name='corporation-select-list'),

    # Genre URLs
    url(r'^genres/$', GenreList.as_view(), name='genre-list'),
    url(r'^genres/(?P<pk>[0-9]+)/$', GenreDetail.as_view(), name='genre-detail'),
    url(r'^select/genres/$', GenreSelectList.as_view(), name='genre-select-list'),

    # Subject URLs
    url(r'^subjects/$', SubjectList.as_view(), name='subject-list'),
    url(r'^subjects/(?P<pk>[0-9]+)/$', SubjectDetail.as_view(), name='subject-detail'),
    url(r'^select/subjects/$', SubjectSelectList.as_view(), name='subject-select-list'),

    # Authority services URLs
    url(r'^wikipedia/$', WikipediaList.as_view(), name='wikipedia-list'),
    url(r'^viaf/$', VIAFList.as_view(), name='viaf-list'),
    url(r'^lcsh/$', LCSHList.as_view(), name='lcsh-list')
]