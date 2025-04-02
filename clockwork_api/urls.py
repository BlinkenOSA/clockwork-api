from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

urlpatterns = [
    path('v1/accession/', include('accession.urls', namespace='accession-v1')),
    path('v1/archival_unit/', include('archival_unit.urls', namespace='archival_unit-v1')),
    path('v1/authority_list/', include('authority.urls', namespace='authority-v1')),
    path('v1/audit_log/', include('audit_log.urls', namespace='audit-log-v1')),
    path('v1/container/', include('container.urls', namespace='container-v1')),
    path('v1/controlled_list/', include('controlled_list.urls', namespace='controlled_list-v1')),
    path('v1/donor/', include('donor.urls', namespace='donor-v1')),
    path('v1/finding_aids/', include('finding_aids.urls', namespace='finding_aids-v1')),
    path('v1/isaar/', include('isaar.urls', namespace='isaar-v1')),
    path('v1/isad/', include('isad.urls', namespace='isad-v1')),
    path('v1/mlr/', include('mlr.urls', namespace='mlr-v1')),
    path('v1/digitization/', include('digitization.urls', namespace='digitization-v1')),
    path('v1/dashboard/', include('dashboard.urls', namespace='dashboard-v1')),
    path('v1/catalog/', include('catalog.urls', namespace='catalog-v1')),
    path('v1/workflow/', include('workflow.urls', namespace='workflow-v1')),
    path('v1/research/', include('research.urls', namespace='research-v1')),

    path('admin/', admin.site.urls),

    # JWT endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    # Debug Toolbar endpoints
    path('__debug__/', include('debug_toolbar.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
