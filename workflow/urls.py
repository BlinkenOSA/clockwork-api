from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from workflow.views.container_views import GetSetDigitizedContainer, GetContainerMetadata, \
    GetContainerMetadataByLegacyID
from workflow.views.digital_object_views import DigitalObjectInfo, DigitalObjectUpsert
from workflow.views.finding_aids_views import GetFAEntityMetadataByItemID
from workflow.views.translation_view import GetTranslationToOriginal, GetTranslationToEnglish

app_name = 'workflow'

schema_view = get_schema_view(
   openapi.Info(
      title="AMS Workflow APIs Documentation",
      default_version='v1',
      description="API documentation of the API endpoints used by the AMS Workflow",
      contact=openapi.Contact(email="bonej@ceu.edu"),
      license=openapi.License(name="BSD License"),
   ),
   validators=['flex'],
   public=True,
   permission_classes=[permissions.AllowAny]
)

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
         name='get_translation'),

    # Get back the data for digital object upload
    path('digital_object/info/<str:digital_object_id>',
         DigitalObjectInfo.as_view(), name='digital_object_info'),
    path('digital_object/upsert/<str:level>/<str:digital_object_id>/',
         DigitalObjectUpsert.as_view(), name='digital_object_upsert'),

    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
