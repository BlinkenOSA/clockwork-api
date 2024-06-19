import csv

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from mlr.models import MLREntity
from mlr.serializers import MLRListSerializer, MLREntitySerializer


class MLRList(generics.ListAPIView):
    queryset = MLREntity.objects.all()
    serializer_class = MLRListSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('name',)

    def filter_queryset(self, queryset):
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


class MLRDetail(RetrieveUpdateAPIView):
    queryset = MLREntity.objects.all()
    serializer_class = MLREntitySerializer


class MLRExportCSV(APIView):
    def get(self, request, *args, **kwargs):
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