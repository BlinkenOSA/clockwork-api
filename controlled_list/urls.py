from django.conf.urls import url
from django.urls import path

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
    path('access_rights/', AccessRightList.as_view(), name='access_rights-list'),
    path('access_rights/<int:pk>/', AccessRightDetail.as_view(), name='access_rights-detail'),
    path('select/access_rights/', AccessRightSelectList.as_view(), name='access_rights-select-list'),
    
    # Archival Unit Theme URLs
    path('archival_unit_themes/', ArchivalUnitThemeList.as_view(), name='archival_unit_themes-list'),
    path('archival_unit_themes/<int:pk>/', ArchivalUnitThemeDetail.as_view(), name='archival_unit_themes-detail'),
    path('select/archival_unit_themes/', ArchivalUnitThemeSelectList.as_view(), name='archival_unit_themes-select-list'),

    # Building URLs
    path('building/', BuildingList.as_view(), name='building-list'),
    path('building/<int:pk>/', BuildingDetail.as_view(), name='building-detail'),
    path('select/building/', BuildingSelectList.as_view(), name='building-select-list'),

    # Carrier Type URLs
    path('carrier_types/', CarrierTypeList.as_view(), name='carrier_type-list'),
    path('carrier_types/<int:pk>/', CarrierTypeDetail.as_view(), name='carrier_type-detail'),
    path('select/carrier_types/', CarrierTypeSelectList.as_view(), name='carrier_type-select-list'),

    # Corporation Role URLs
    path('corporation_roles/', CorporationRoleList.as_view(), name='corporation_role-list'),
    path('corporation_roles/<int:pk>/', CorporationRoleDetail.as_view(), name='corporation_role-detail'),
    path('select/corporation_roles/', CorporationRoleSelectList.as_view(), name='corporation_role-select-list'),

    # Date Type URLs
    path('date_types/', DateTypeList.as_view(), name='date_type-list'),
    path('date_types/<int:pk>/', DateTypeDetail.as_view(), name='date_type-detail'),
    path('select/date_types/', DateTypeSelectList.as_view(), name='date_type-select-list'),

    # Extent Unit URLs
    path('extent_units/', ExtentUnitList.as_view(), name='extent_unit-list'),
    path('extent_units/<int:pk>/', ExtentUnitDetail.as_view(), name='extent_unit-detail'),
    path('select/extent_units/', ExtentUnitSelectList.as_view(), name='extent_unit-select-list'),

    # Geo Role URLs
    path('geo_roles/', GeoRoleList.as_view(), name='geo_role-list'),
    path('geo_roles/<int:pk>/', GeoRoleDetail.as_view(), name='geo_role-detail'),
    path('select/geo_roles/', GeoRoleSelectList.as_view(), name='geo_role-select-list'),

    # Keyword URLs
    path('keywords/', KeywordList.as_view(), name='keyword-list'),
    path('keywords/<int:pk>/', KeywordDetail.as_view(), name='keyword-detail'),
    path('select/keywords/', KeywordSelectList.as_view(), name='keyword-select-list'),

    # Language Usage URLs
    path('language_usages/', LanguageUsageList.as_view(), name='language_usage-list'),
    path('language_usages/<int:pk>/', LanguageUsageDetail.as_view(), name='language_usage-detail'),
    path('select/language_usages/', LanguageUsageSelectList.as_view(), name='language_usage-select-list'),

    # Locale URLs
    path('locales/', LocaleList.as_view(), name='locale-list'),
    path('locales/<int:pk>/', LocaleDetail.as_view(), name='locale-detail'),
    path('select/locales/', LocaleSelectList.as_view(), name='locale-select-list'),

    # Person Role URLs
    path('person_roles/', PersonRoleList.as_view(), name='person_role-list'),
    path('person_roles/<int:pk>/', PersonRoleDetail.as_view(), name='person_role-detail'),
    path('select/person_roles/', PersonRoleSelectList.as_view(), name='person_role-select-list'),

    # Primary Type URLs
    path('primary_types/', PrimaryTypeList.as_view(), name='primary_type-list'),
    path('primary_types/<int:pk>/', PrimaryTypeDetail.as_view(), name='primary_type-detail'),
    path('select/primary_types/', PrimaryTypeSelectList.as_view(), name='primary_type-select-list'),

    # Reproduction Right URLs
    path('reproduction_rights/', ReproductionRightList.as_view(), name='reproduction_right-list'),
    path('reproduction_rights/<int:pk>/', ReproductionRightDetail.as_view(), name='reproduction_right-detail'),
    path('select/reproduction_rights/', ReproductionRightSelectList.as_view(), name='reproduction_right-select-list'),

    # Rights Restriction Reason URLs
    path('rights_restriction/', RightsRestrictionReasonList.as_view(), name='rights_restriction-list'),
    path('rights_restriction/<int:pk>/', RightsRestrictionReasonDetail.as_view(), name='rights_restriction-detail'),
    path('select/rights_restriction/', RightsRestrictionReasonSelectList.as_view(), name='rights_restriction-select-list'),
]