from django.conf.urls import url

from authority.views.country_views import CountryList, CountryDetail, CountrySelectList
from authority.views.language_views import LanguageList, LanguageDetail, LanguageSelectList
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

    # Authority services URLs
    url(r'^wikipedia/$', WikipediaList.as_view(), name='wikipedia-list')
]