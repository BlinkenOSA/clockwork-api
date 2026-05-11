from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from workflow.views.digital_object_info_views import DigitalObjectInfoView
from workflow.views.digital_object_upsert_views import DigitalObjectUpsert
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
    # Used by admin UI to translate documents
    path('translate_to_original/', GetTranslationToOriginal.as_view(),
         name='get_translation'),
    path('translate_to_english/', GetTranslationToEnglish.as_view(),
         name='get_translation'),

    # Used by the workflow to get information about a digital object based on its file name
    path('digital_object/info/<str:file_name>',
         DigitalObjectInfoView.as_view(), name='digital_object_info'),

    path('digital_object/upsert/master/<str:file_name>',
         DigitalObjectUpsert.as_view(type='master'), name='digital_object_master_upsert'),
    path('digital_object/upsert/access/catalog/<str:file_name>',
         DigitalObjectUpsert.as_view(type='access-catalog'), name='digital_object_access_copy_upsert_catalog'),
    path('digital_object/upsert/access/rc/<str:file_name>',
         DigitalObjectUpsert.as_view(type='access-rc'), name='digital_object_access_copy_upsert_rc'),

    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
