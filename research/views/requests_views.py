import datetime
import json

import requests
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from pymarc import MARCReader
from pymarc.reader import JSONReader
from requests.auth import HTTPBasicAuth
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSeriesSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from clockwork_api.pagination import DropDownResultSetPagination
from container.models import Container
from research.models import RequestItem, Request
from research.serializers.requests_serializers import RequestListSerializer, ContainerListSerializer, \
    RequestCreateSerializer, RequestItemWriteSerializer, RequestItemReadSerializer
from django_filters import rest_framework as filters
from hashids import Hashids

class RequestFilterClass(filters.FilterSet):
    researcher = filters.CharFilter(label='Researcher', method='filter_researcher')
    status = filters.CharFilter(label='Status', method='filter_status')
    item_origin = filters.CharFilter(label='Item Origin', method='filter_item_origin')
    request_date = filters.CharFilter(label='Request Date', method='filter_request_date')

    def filter_researcher(self, queryset, name, value):
        return queryset.filter(request__researcher=value)

    def filter_status(self, queryset, name, value):
        return queryset.filter(status=value)

    def filter_item_origin(self, queryset, name, value):
        return queryset.filter(item_origin=value)

    def filter_request_date(self, queryset, name, value):
        if value == 'today':
            return queryset.filter(request__request_date__date=datetime.date.today())
        if value == 'all':
            return queryset
        if value == 'next_day':
            today = datetime.date.today()
            if today.weekday() < 4:
                next_weekday = today + datetime.timedelta(days=1)
            else:
                next_weekday = today + datetime.timedelta(days=7 - today.weekday())
            return queryset.filter(request__request_date__date=next_weekday)
        if value == 'next_week':
            today = datetime.date.today()
            next_week_start = today + datetime.timedelta(days=7 - today.weekday())
            next_week_end = today + datetime.timedelta(days=14 - today.weekday())
            return queryset.filter(
                request__request_date__date__gte=next_week_start,
                request__request_date__date__lt=next_week_end,
            )


class RequestsList(generics.ListAPIView):
    queryset = RequestItem.objects.all().order_by('-request__created_date')
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = RequestFilterClass
    search_fields = ['request__researcher__last_name', 'request__researcher__first_name',
                     'container__archival_unit__reference_code', 'identifier', 'title',
                     'container__barcode']
    ordering_fields = ['request__researcher__last_name', 'status', 'item_origin', 'request__request_date',
                       'ordering', 'reshelve_date']
    serializer_class = RequestListSerializer


class RequestsCreate(CreateAPIView):
    serializer_class = RequestCreateSerializer
    queryset = Request.objects.all()


class RequestItemRetrieveUpdate(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    method_serializer_classes = {
        ('GET', ): RequestItemReadSerializer,
        ('PUT', ): RequestItemWriteSerializer
    }
    queryset = RequestItem.objects.all()


class RequestsListForPrint(generics.ListAPIView):
    serializer_class = RequestListSerializer
    pagination_class = None

    def get_queryset(self):
        return RequestItem.objects.filter(
            status='2'
        ).order_by('request__request_date')


class RequestItemStatusStep(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        request_item_id = self.kwargs.get('request_item_id')
        request_item = get_object_or_404(RequestItem, pk=request_item_id)
        st = int(request_item.status)

        if action == 'next':
            # Handle digital version
            if request_item.container:
                if request_item.container.has_digital_version:
                    if st == 2:
                        request_item.status = '9'
                        request_item.save()
                else:
                    if st < 5:
                        request_item.status = str(st+1)
                        request_item.save()
            else:
                if st < 5:
                    request_item.status = str(st + 1)
                    request_item.save()

            # Check if all the items were delivered, if yes send out the e-mail to the user
            if request_item.status == '3' or request_item.status == '9':
                request = request_item.request
                mail = EmailWithTemplate(
                    researcher=request.researcher,
                    context={
                        'researcher': request.researcher,
                        'request': request,
                        'item': request_item
                    }
                )
                mail.send_request_delivered_user()

            return Response(status=status.HTTP_200_OK)
        if action == 'previous':
            if 1 < st < 5:
                request_item.status = str(st-1)
                request_item.save()
            return Response(status=status.HTTP_200_OK)


class RequestSeriesSelect(generics.ListAPIView):
    queryset = ArchivalUnit.objects.filter(level='S').order_by('sort')
    filter_backends = [SearchFilter]
    search_fields = ['title_full']
    pagination_class = DropDownResultSetPagination
    serializer_class = ArchivalUnitSeriesSerializer


class RequestContainerSelect(generics.ListAPIView):
    filter_backends = [SearchFilter]
    search_fields = ['container_no']
    pagination_class = DropDownResultSetPagination
    serializer_class = ContainerListSerializer

    def get_queryset(self):
        series_id = self.kwargs['series_id']
        return Container.objects.filter(archival_unit__id=series_id).order_by('container_no')


class RequestLibraryMLR(APIView):
    def get(self, request, *args, **kwargs):
        koha_id = self.kwargs['koha_id']
        hashids = Hashids(salt="osalibrary", min_length=8)
        solr_id = hashids.encode(int(koha_id))

        solr_core = getattr(settings, "SOLR_CORE_CATALOG_NEW", "catalog")
        solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), solr_core)

        r = requests.get(
            url="%s/select?q=id:%s" % (solr_url, solr_id),
            auth=HTTPBasicAuth(getattr(settings, 'SOLR_USERNAME'), getattr(settings, 'SOLR_PASSWORD'))
        )
        if r.status_code == 200:
            response = r.json()
            if response['response']['numFound'] > 0:
                marc = json.loads(response['response']['docs'][0]['marc'])
                field580 = list(filter(lambda x: '580' in x, marc['fields']))
                items = list(filter(lambda x: '952' in x, marc['fields']))

                locations = self._get_locations(items)
                collections = self._get_collections(field580)

                if len(locations) == 0:
                    return Response(", ".join(collections))

                if len(collections) == 0:
                    return Response(", ".join(locations))

                return Response('%s / %s' % (", ".join(collections), ", ".join(locations)))
        else:
            Response(status=r.status_code)

    def _get_locations(self, items):
        locations = set()
        for item in items:
            subfields = list(filter(lambda sf: 'c' in sf, item['952']['subfields']))
            if subfields:
                locations.add(subfields[0]['c'])
            else:
                locations.add("General collection")
        return locations

    def _get_collections(self, fields):
        collections = set()
        for field in fields:
            for sf in field['580']['subfields']:
                if 'a' in sf:
                    collections.add(sf['a'])
        return collections