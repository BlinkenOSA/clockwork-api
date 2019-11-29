from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="Clockwork API Documentation",
      default_version='v1',
      description="API documentation of the API serving the Clockwork Archival Management System",
      contact=openapi.Contact(email="bonej@ceu.edu"),
      license=openapi.License(name="BSD License"),
   ),
   validators=['flex'],
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('v1/accession/', include('accession.urls', namespace='accession-v1')),
    path('v1/archival_unit/', include('archival_unit.urls', namespace='archival_unit-v1')),
    path('v1/authority/', include('authority.urls', namespace='authority-v1')),
    path('v1/container/', include('container.urls', namespace='container-v1')),
    path('v1/controlled_list/', include('controlled_list.urls', namespace='controlled_list-v1')),
    path('v1/donor/', include('donor.urls', namespace='donor-v1')),
    path('v1/finding_aids/', include('finding_aids.urls', namespace='finding_aids-v1')),
    path('v1/isaar/', include('isaar.urls', namespace='isaar-v1')),
    path('v1/isad/', include('isad.urls', namespace='isad-v1')),
    path('admin/', admin.site.urls),

    # Swagger endpoints
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=None),
      name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=None), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=None), name='schema-redoc'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
