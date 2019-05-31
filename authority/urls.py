from django.conf.urls import url

from authority.views.country_views import CountryList, CountryDetail, CountrySelectList

app_name = 'authority'

urlpatterns = [
    url(r'^countries/$', CountryList.as_view(), name='country-list'),
    url(r'^countries/(?P<pk>[0-9]+)/$', CountryDetail.as_view(), name='country-detail'),

    url(r'^select/countries/$', CountrySelectList.as_view(), name='country-select-list'),
]