from django.urls import path

from authority.views.corporation_views import CorporationList, CorporationDetail, CorporationSelectList
from authority.views.country_views import CountryList, CountryDetail, CountrySelectList
from authority.views.genre_views import GenreList, GenreDetail, GenreSelectList
from authority.views.language_views import LanguageList, LanguageDetail, LanguageSelectList
from authority.views.person_views import PersonList, PersonDetail, PersonSelectList
from authority.views.place_views import PlaceList, PlaceDetail, PlaceSelectList
from authority.views.lcsh_views import LCSHList
from authority.views.similarity_views.person_similarity_views import PersonSimilarById, PersonSimilarMerge
from authority.views.subject_views import SubjectList, SubjectDetail, SubjectSelectList
from authority.views.viaf_views import VIAFList
from authority.views.wikidata_views import WikidataList
from authority.views.wikipedia_views import WikipediaList

app_name = 'authority'

urlpatterns = [
    # Country URLs
    path('countries/', CountryList.as_view(), name='country-list'),
    path('countries/<int:pk>/', CountryDetail.as_view(), name='country-detail'),
    path('select/countries/', CountrySelectList.as_view(), name='country-select-list'),

    # Language URLs
    path('languages/', LanguageList.as_view(), name='language-list'),
    path('languages/<int:pk>/', LanguageDetail.as_view(), name='language-detail'),
    path('select/languages/', LanguageSelectList.as_view(), name='language-select-list'),

    # Place URLs
    path('places/', PlaceList.as_view(), name='place-list'),
    path('places/<int:pk>/', PlaceDetail.as_view(), name='place-detail'),
    path('select/places/', PlaceSelectList.as_view(), name='place-select-list'),

    # Person URLs
    path('people/', PersonList.as_view(), name='person-list'),
    path('people/<int:pk>/', PersonDetail.as_view(), name='person-detail'),
    path('select/people/', PersonSelectList.as_view(), name='person-select-list'),

    path("people/<int:pk>/similar/", PersonSimilarById.as_view(), name="person-similar-by-id"),
    path("people/merge/", PersonSimilarMerge.as_view(), name='person-merge'),

    # Corporation URLs
    path('corporations/', CorporationList.as_view(), name='corporation-list'),
    path('corporations/<int:pk>/', CorporationDetail.as_view(), name='corporation-detail'),
    path('select/corporations/', CorporationSelectList.as_view(), name='corporation-select-list'),

    # Genre URLs
    path('genres/', GenreList.as_view(), name='genre-list'),
    path('genres/<int:pk>/', GenreDetail.as_view(), name='genre-detail'),
    path('select/genres/', GenreSelectList.as_view(), name='genre-select-list'),

    # Subject URLs
    path('subjects/', SubjectList.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', SubjectDetail.as_view(), name='subject-detail'),
    path('select/subjects/', SubjectSelectList.as_view(), name='subject-select-list'),

    # Authority services URLs
    path('wikipedia/', WikipediaList.as_view(), name='wikipedia-list'),
    path('wikidata/', WikidataList.as_view(), name='wikidata-list'),
    path('viaf/', VIAFList.as_view(), name='viaf-list'),
    path('lcsh/', LCSHList.as_view(), name='lcsh-list')
]