from django.urls import path

from catalog.views.archival_unit_views.archival_units_detail_view import ArchivalUnitsDetailView
from catalog.views.finding_aids_views.finding_aids_entity_detail_view import FindingAidsEntityDetailView
from catalog.views.finding_aids_views.finding_aids_entity_location_view import FindingAidsEntityLocationView
from catalog.views.iiif_views.archival_units_image_manifest_view import ArchivalUnitsManifestView
from catalog.views.iiif_views.finding_aids_image_manifest_view import FindingAidsImageManifestView
from catalog.views.research_request_views.researcher_registration import ResearcherRegistration
from catalog.views.tree_views.archival_units_tree_quick_view import ArchivalUnitsTreeQuickView
from catalog.views.tree_views.archival_units_tree_view import ArchivalUnitsTreeView
from research.views.researcher_views import ResearcherCountrySelectList, ResearcherNationalitySelectList
from research.views.researher_degree_views import ResearcherDegreeSelectList

app_name = 'catalog'

urlpatterns = [
    # Archival Unit Views
    path('archival-units/<str:archival_unit_id>', ArchivalUnitsDetailView.as_view(),
         name='archival-units-full-view'),

    # Finding Aids Views
    path('finding-aids/<str:fa_entity_catalog_id>', FindingAidsEntityDetailView.as_view(),
         name='finding-aids-full-view'),
    path('finding-aids-location/<str:fa_entity_catalog_id>', FindingAidsEntityLocationView.as_view(),
         name='finding-aids-location-view'),

    # Tree Views
    path('archival-units-tree/<str:archival_unit_id>', ArchivalUnitsTreeView.as_view(),
         name='archival-units-tree'),
    path('archival-units-tree-quick-view/<str:archival_unit_id>', ArchivalUnitsTreeQuickView.as_view(),
         name='archival-units-tree-quick-view'),

    # IIIF manifests
    path('archival-units-image-manifest/<str:archival_unit_id>/manifest.json',
         ArchivalUnitsManifestView.as_view(),
         name='archival-units-manifest-view'),
    path('finding-aids-image-manifest/(<str:fa_entity_catalog_id>/manifest.json',
         FindingAidsImageManifestView.as_view(),
         name='finding-aids-manifest-view'),

    # Research Registration
    path('register-researcher/', ResearcherRegistration.as_view(), name='researcher-rigistration'),
    path('research/degree/select/', ResearcherDegreeSelectList.as_view(), name='researcher-degree-select-list'),
    path('research/country/select/', ResearcherCountrySelectList.as_view(), name='researcher-country-select-list'),
    path('research/nationality/select/', ResearcherNationalitySelectList.as_view(), name='researcher-country-select-list')
]
