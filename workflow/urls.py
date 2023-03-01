from django.urls import path

from workflow.views.container_views import GetSetDigitizedContainer, GetContainerMetadata, \
    GetContainerMetadataByLegacyID
from workflow.views.finding_aids_views import GetFAEntityMetadataByItemID
from workflow.views.translation_view import GetTranslationToOriginal, GetTranslationToEnglish

app_name = 'workflow'

urlpatterns = [
    # Used by the digitization workflow to push technical metadata
    path('containers/<str:barcode>/', GetSetDigitizedContainer.as_view(),
         name='list_set_digitized_container'),

    # Used by the digitization workflow to collect descriptive metadata
    path('containers/metadata/<str:barcode>/', GetContainerMetadata.as_view(),
         name='list_get_container_metadata'),

    # Used by research-cloud-upload workflow
    path('containers/by-legacy-id/<str:legacy_id>/', GetContainerMetadataByLegacyID.as_view(),
         name='get_container_by_legacy_id'),

    # Used by research-cloud-upload workflow
    path('finding_aids/by-item-id/<str:item_id>/', GetFAEntityMetadataByItemID.as_view(),
         name='get_fa_entity_by_item_id'),

    # Used by admin UI to translate documents
    path('translate_to_original/', GetTranslationToOriginal.as_view(),
         name='get_translation'),
    path('translate_to_english/', GetTranslationToEnglish.as_view(),
         name='get_translation')
]
