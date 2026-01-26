import csv

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from mlr.models import MLREntity
from mlr.serializers import MLRListSerializer, MLREntitySerializer


class MLRList(generics.ListAPIView):
    """
    Lists Master Location Register (MLR) entries with query-parameter filtering.

    This endpoint returns :class:`mlr.models.MLREntity` records serialized with
    :class:`mlr.serializers.MLRListSerializer`.

    Filtering
    ---------
    Filtering is implemented by overriding :meth:`filter_queryset` and supports:

        - ``fonds``: archival unit PK; filters by fonds number (``series__fonds``)
        - ``carrier_type``: carrier type PK
        - ``building``: building PK (via related locations)
        - ``module``: integer (via related locations)
        - ``row``: integer (via related locations)
        - ``section``: integer (via related locations)
        - ``shelf``: integer (via related locations)

    Notes
    -----
    ``search_fields`` is configured as ``('name',)`` but :class:`MLREntity` does
    not define a ``name`` field. If search is expected to work, this likely
    should be updated (e.g., to ``series__title`` or ``series__reference_code``).
    """

    queryset = MLREntity.objects.all()
    serializer_class = MLRListSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('name',)

    def filter_queryset(self, queryset):
        """
        Applies query-parameter filtering to the base queryset.

        Parameters
        ----------
        queryset : django.db.models.QuerySet
            Base queryset provided by the view.

        Returns
        -------
        django.db.models.QuerySet
            Filtered queryset.
        """
        qs = queryset

        fonds = self.request.query_params.get('fonds', None)
        if fonds:
            archival_unit = get_object_or_404(ArchivalUnit, pk=fonds)
            qs = qs.filter(series__fonds=archival_unit.fonds)

        carrier_type = self.request.query_params.get('carrier_type', None)
        if carrier_type:
            qs = qs.filter(carrier_type=carrier_type)

        building = self.request.query_params.get('building', None)
        if building:
            qs = qs.filter(locations__building=building)

        module = self.request.query_params.get('module', None)
        if module:
            qs = qs.filter(locations__module=module)

        row = self.request.query_params.get('row', None)
        if row:
            qs = qs.filter(locations__row=row)

        section = self.request.query_params.get('section', None)
        if section:
            qs = qs.filter(locations__section=section)

        shelf = self.request.query_params.get('shelf', None)
        if shelf:
            qs = qs.filter(locations__shelf=shelf)

        return qs


class MLRDetail(AuditLogMixin, RetrieveUpdateAPIView):
    """
    Retrieves and updates a single Master Location Register (MLR) entry.

    Uses :class:`mlr.serializers.MLREntitySerializer`, which supports nested
    updates for related :class:`mlr.models.MLREntityLocation` records.

    Notes
    -----
    The endpoint supports:
        - GET: retrieve MLR entry
        - PUT/PATCH: update MLR entry (including nested locations)
    """

    queryset = MLREntity.objects.all()
    serializer_class = MLREntitySerializer


class MLRExportCSV(APIView):
    """
    Exports Master Location Register (MLR) entries as a CSV file.

    The exported CSV includes the following columns:
        - ``series``: series reference code
        - ``carrier``: carrier type label
        - ``locations``: formatted location string (see :meth:`MLREntity.get_locations`)

    Query Parameters
    ---------------
    fonds_id : int, optional
        Archival unit PK used to filter by fonds. The export is restricted to
        series-level units (``level='S'``) under the fonds.
    module : int, optional
        Filters by location module.
    row : int, optional
        Filters by location row.
    section : int, optional
        Filters by location section.
    shelf : int, optional
        Filters by location shelf.

    Notes
    -----
    The current implementation filters ``row``, ``section``, and ``shelf`` using
    ``locations__module`` (likely a copy/paste bug). If those filters are
    intended to work, they likely should be:
        - row -> ``locations__row``
        - section -> ``locations__section``
        - shelf -> ``locations__shelf``
    """

    def get(self, request, *args, **kwargs):
        """
        Builds the filtered queryset and streams a CSV response.
        """
        qs = MLREntity.objects.all().order_by('series__sort', 'carrier_type__type')
        file_name = 'mlr'

        if 'fonds_id' in request.GET:
            archival_unit = ArchivalUnit.objects.get(id=request.GET['fonds_id'])
            qs = qs.filter(
                series__level='S',
                series__fonds=archival_unit.fonds
            ).order_by('series__sort', 'carrier_type__type')
            file_name += "-hu_osa_%s" % archival_unit.fonds

        if 'module' in request.GET:
            qs = qs.filter(locations__module=request.GET['module'])
            file_name += "-module_%s" % request.GET['module']

        if 'row' in request.GET:
            qs = qs.filter(locations__module=request.GET['row'])
            file_name += "-row_%s" % request.GET['row']

        if 'section' in request.GET:
            qs = qs.filter(locations__module=request.GET['section'])
            file_name += "-section_%s" % request.GET['section']

        if 'shelf' in request.GET:
            qs = qs.filter(locations__module=request.GET['shelf'])
            file_name += "-shelf_%s" % request.GET['shelf']

        file_name += ".csv"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name

        field_names = ['series', 'carrier', 'locations']

        writer = csv.DictWriter(response, delimiter=str(u";"), fieldnames=field_names)
        writer.writeheader()

        for mlr in qs:
            writer.writerow({
                'series': mlr.series.reference_code,
                'carrier': mlr.carrier_type.type,
                'locations': mlr.get_locations()
            })

        return response
