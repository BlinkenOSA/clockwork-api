from django.urls import path, re_path

from catalog.views.archival_unit_views.archival_units_detail_view import ArchivalUnitsDetailView, \
    ArchivalUnitsFacetQuickView, ArchivalUnitsHelperView
from catalog.views.facet_info_views.wikidata_view import WikidataView
from catalog.views.finding_aids_views.finding_aids_entity_detail_view import FindingAidsEntityDetailView
from catalog.views.finding_aids_views.finding_aids_entity_location_view import FindingAidsEntityLocationView
from catalog.views.iiif_views.archival_units_image_manifest_view import ArchivalUnitsManifestView
from catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view import FindingAidsIIFPresentationV3View
from catalog.views.iiif_views.finding_aids_image_manifest_view import FindingAidsImageManifestView
from catalog.views.research_request_views.request_views import ResearcherRequestView
from catalog.views.research_request_views.researcher_forgot_card_number import ResearcherForgotCardNumber
from catalog.views.research_request_views.researcher_registration import ResearcherRegistration
from catalog.views.statistics_views.archival_unit_sizes import ArchivalUnitSizes
from catalog.views.statistics_views.collection_specific_tags import CollectionSpecificTags
from catalog.views.statistics_views.newly_added_content import NewlyAddedContent
from catalog.views.tree_views.archival_units_tree_quick_view import ArchivalUnitsTreeQuickView
from catalog.views.tree_views.archival_units_tree_view_v2 import ArchivalUnitsTreeViewV2
from research.views.researcher_views import ResearcherCountrySelectList, ResearcherNationalitySelectList
from research.views.researcher_degree_views import ResearcherDegreeSelectList

app_name = 'catalog'

urlpatterns = [
    # Archival Unit Views
    path('archival-units/<str:archival_unit_id>/', ArchivalUnitsDetailView.as_view(),
         name='archival-units-full-view'),
    path('image-gallery/archival-unit/', ArchivalUnitsFacetQuickView.as_view(),
         name='archival-units-facet-quick-view'),
    path('archival-units/by-reference-code/<str:reference_code>/', ArchivalUnitsHelperView.as_view()),

    # Finding Aids Views
    path('finding-aids/<str:fa_entity_catalog_id>/', FindingAidsEntityDetailView.as_view(),
         name='finding-aids-full-view'),
    path('finding-aids-location/<str:fa_entity_catalog_id>/', FindingAidsEntityLocationView.as_view(),
         name='finding-aids-location-view'),

    # Tree Views
    path('archival-units-tree/<str:archival_unit_id>/', ArchivalUnitsTreeViewV2.as_view(), kwargs={'theme': None},
         name='archival-units-tree'),
    path('archival-units-tree/<str:archival_unit_id>/<str:theme>/', ArchivalUnitsTreeViewV2.as_view(),
         name='archival-units-tree-with-theme'),
    path('archival-units-tree-quick-view/<str:archival_unit_id>/', ArchivalUnitsTreeQuickView.as_view(),
         name='archival-units-tree-quick-view'),

    # Wikidata
    path('wikidata/<str:wikidata_id>/', WikidataView.as_view(), name='wikidata_view'),

    # IIIF manifests
    path('archival-units-image-manifest/<str:archival_unit_id>/manifest.json',
         ArchivalUnitsManifestView.as_view(),
         name='archival-units-manifest-view'),
    path('finding-aids-image-manifest/<str:fa_entity_catalog_id>/manifest.json',
         FindingAidsIIFPresentationV3View.as_view(),
         name='finding-aids-manifest-view'),
    path('finding-aids-image-manifest/mobile/<str:fa_entity_catalog_id>/manifest.json',
         FindingAidsImageManifestView.as_view(),
         name='finding-aids-manifest-mobile-view'),

    # Research Registration
    path('register-researcher/', ResearcherRegistration.as_view(), name='researcher-rigistration'),
    path('research/degree/select/', ResearcherDegreeSelectList.as_view(), name='researcher-degree-select-list'),
    path('research/country/select/', ResearcherCountrySelectList.as_view(), name='researcher-country-select-list'),
    path('research/nationality/select/', ResearcherNationalitySelectList.as_view(), name='researcher-country-select-list'),

    path('researcher-card-number/', ResearcherForgotCardNumber.as_view(), name='researcher-forgot-card-number'),

    # New Request
    path('request/', ResearcherRequestView.as_view(), name='new-request'),

    # Statistics
    re_path(r'newly-added-content/(?P<content_type>["isad"|"folder"]+)/$', NewlyAddedContent.as_view(),
            name='newly-added-content'),
    path('archival-unit-sizes/', ArchivalUnitSizes.as_view(), name='archival-unit-sizes'),
    path('collection-specific-tags/', CollectionSpecificTags.as_view(), name='collection-specific-tags')
]
