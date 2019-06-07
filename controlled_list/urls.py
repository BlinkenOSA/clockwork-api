from django.conf.urls import url

from controlled_list.views.access_right_views import AccessRightList, AccessRightDetail, AccessRightSelectList
from controlled_list.views.archival_unit_theme_views import ArchivalUnitThemeList, ArchivalUnitThemeDetail, \
    ArchivalUnitThemeSelectList
from controlled_list.views.building_views import BuildingList, BuildingDetail, BuildingSelectList
from controlled_list.views.carrier_type_views import CarrierTypeList, CarrierTypeDetail, CarrierTypeSelectList
from controlled_list.views.corporation_role_views import CorporationRoleList, CorporationRoleDetail, \
    CorporationRoleSelectList
from controlled_list.views.date_type_views import DateTypeList, DateTypeDetail, DateTypeSelectList
from controlled_list.views.extent_unit_views import ExtentUnitList, ExtentUnitDetail, ExtentUnitSelectList
from controlled_list.views.geo_role_views import GeoRoleList, GeoRoleDetail, GeoRoleSelectList
from controlled_list.views.keyword_views import KeywordList, KeywordDetail, KeywordSelectList
from controlled_list.views.language_usage_views import LanguageUsageList, LanguageUsageDetail, LanguageUsageSelectList
from controlled_list.views.locale_views import LocaleList, LocaleDetail, LocaleSelectList
from controlled_list.views.person_role_views import PersonRoleList, PersonRoleDetail, PersonRoleSelectList
from controlled_list.views.primary_type_views import PrimaryTypeList, PrimaryTypeDetail, PrimaryTypeSelectList
from controlled_list.views.reproduction_right_views import ReproductionRightList, ReproductionRightDetail, \
    ReproductionRightSelectList
from controlled_list.views.rights_restriction_reason_views import RightsRestrictionReasonDetail, \
    RightsRestrictionReasonSelectList, RightsRestrictionReasonList

app_name = 'controlled_list'

urlpatterns = [
    # Access Rights URLs
    url(r'^access_rights/$', AccessRightList.as_view(), name='access_rights-list'),
    url(r'^access_rights/(?P<pk>[0-9]+)/$', AccessRightDetail.as_view(), name='access_rights-detail'),
    url(r'^select/access_rights/$', AccessRightSelectList.as_view(), name='access_rights-select-list'),
    
    # Archival Unit Theme URLs
    url(r'^archival_unit_themes/$', ArchivalUnitThemeList.as_view(), name='archival_unit_themes-list'),
    url(r'^archival_unit_themes/(?P<pk>[0-9]+)/$', ArchivalUnitThemeDetail.as_view(), name='archival_unit_themes-detail'),
    url(r'^select/archival_unit_themes/$', ArchivalUnitThemeSelectList.as_view(), name='archival_unit_themes-select-list'),

    # Building URLs
    url(r'^building/$', BuildingList.as_view(), name='building-list'),
    url(r'^building/(?P<pk>[0-9]+)/$', BuildingDetail.as_view(), name='building-detail'),
    url(r'^select/building/$', BuildingSelectList.as_view(), name='building-select-list'),

    # Carrier Type URLs
    url(r'^carrier_types/$', CarrierTypeList.as_view(), name='carrier_type-list'),
    url(r'^carrier_types/(?P<pk>[0-9]+)/$', CarrierTypeDetail.as_view(), name='carrier_type-detail'),
    url(r'^select/carrier_types/$', CarrierTypeSelectList.as_view(), name='carrier_type-select-list'),

    # Corporation Role URLs
    url(r'^corporation_roles/$', CorporationRoleList.as_view(), name='corporation_role-list'),
    url(r'^corporation_roles/(?P<pk>[0-9]+)/$', CorporationRoleDetail.as_view(), name='corporation_role-detail'),
    url(r'^select/corporation_roles/$', CorporationRoleSelectList.as_view(), name='corporation_role-select-list'),

    # Date Type URLs
    url(r'^date_types/$', DateTypeList.as_view(), name='date_type-list'),
    url(r'^date_types/(?P<pk>[0-9]+)/$', DateTypeDetail.as_view(), name='date_type-detail'),
    url(r'^select/date_types/$', DateTypeSelectList.as_view(), name='date_type-select-list'),

    # Extent Unit URLs
    url(r'^extent_units/$', ExtentUnitList.as_view(), name='extent_unit-list'),
    url(r'^extent_units/(?P<pk>[0-9]+)/$', ExtentUnitDetail.as_view(), name='extent_unit-detail'),
    url(r'^select/extent_units/$', ExtentUnitSelectList.as_view(), name='extent_unit-select-list'),

    # Geo Role URLs
    url(r'^geo_roles/$', GeoRoleList.as_view(), name='geo_role-list'),
    url(r'^geo_roles/(?P<pk>[0-9]+)/$', GeoRoleDetail.as_view(), name='geo_role-detail'),
    url(r'^select/geo_roles/$', GeoRoleSelectList.as_view(), name='geo_role-select-list'),

    # Keyword URLs
    url(r'^keywords/$', KeywordList.as_view(), name='keyword-list'),
    url(r'^keywords/(?P<pk>[0-9]+)/$', KeywordDetail.as_view(), name='keyword-detail'),
    url(r'^select/keywords/$', KeywordSelectList.as_view(), name='keyword-select-list'),

    # Language Usage URLs
    url(r'^language_usages/$', LanguageUsageList.as_view(), name='language_usage-list'),
    url(r'^language_usages/(?P<pk>[0-9]+)/$', LanguageUsageDetail.as_view(), name='language_usage-detail'),
    url(r'^select/language_usages/$', LanguageUsageSelectList.as_view(), name='language_usage-select-list'),

    # Locale URLs
    url(r'^locales/$', LocaleList.as_view(), name='locale-list'),
    url(r'^locales/(?P<pk>[0-9]+)/$', LocaleDetail.as_view(), name='locale-detail'),
    url(r'^select/locales/$', LocaleSelectList.as_view(), name='locale-select-list'),

    # Person Role URLs
    url(r'^person_roles/$', PersonRoleList.as_view(), name='person_role-list'),
    url(r'^person_roles/(?P<pk>[0-9]+)/$', PersonRoleDetail.as_view(), name='person_role-detail'),
    url(r'^select/person_roles/$', PersonRoleSelectList.as_view(), name='person_role-select-list'),

    # Primary Type URLs
    url(r'^primary_types/$', PrimaryTypeList.as_view(), name='primary_type-list'),
    url(r'^primary_types/(?P<pk>[0-9]+)/$', PrimaryTypeDetail.as_view(), name='primary_type-detail'),
    url(r'^select/primary_types/$', PrimaryTypeSelectList.as_view(), name='primary_type-select-list'),

    # Reproduction Right URLs
    url(r'^reproduction_rights/$', ReproductionRightList.as_view(), name='reproduction_right-list'),
    url(r'^reproduction_rights/(?P<pk>[0-9]+)/$', ReproductionRightDetail.as_view(), name='reproduction_right-detail'),
    url(r'^select/reproduction_rights/$', ReproductionRightSelectList.as_view(), name='reproduction_right-select-list'),

    # Rights Restriction Reason URLs
    url(r'^rights_restriction/$', RightsRestrictionReasonList.as_view(), name='rights_restriction-list'),
    url(r'^rights_restriction/(?P<pk>[0-9]+)/$', RightsRestrictionReasonDetail.as_view(), name='rights_restriction-detail'),
    url(r'^select/rights_restriction/$', RightsRestrictionReasonSelectList.as_view(), name='rights_restriction-select-list'),
]