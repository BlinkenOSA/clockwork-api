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
from research.models import RequestItem, Request, RequestItemPart
from research.serializers.requests_serializers import RequestListSerializer, ContainerListSerializer, \
    RequestCreateSerializer, RequestItemWriteSerializer, RequestItemReadSerializer
from django_filters import rest_framework as filters
from hashids import Hashids

from research.serializers.restricted_requests_serializers import RestrictedRequestsListSerializer


class RestrictedRequestFilterClass(filters.FilterSet):
    researcher = filters.CharFilter(label='Researcher', method='filter_researcher')
    status = filters.CharFilter(label='Status', method='filter_status')
    request_date = filters.CharFilter(label='Request Date', method='filter_request_date')

    def filter_researcher(self, queryset, name, value):
        return queryset.filter(request__researcher=value)

    def filter_status(self, queryset, name, value):
        return queryset.filter(status=value)

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


class RestrictedRequestsList(generics.ListAPIView):
    queryset = (RequestItemPart.objects.filter(
        finding_aids_entity__access_rights__statement='Restricted',
        request_item__request__request_date__gte='2025-01-01'
    )
                .order_by('-request_item__request__created_date'))
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = RestrictedRequestFilterClass
    search_fields = ['request_item__request__researcher__last_name', 'request_item__request__researcher__first_name',
                     'request_item__container__archival_unit__reference_code',
                     'request_item__container__barcode']
    ordering_fields = ['request_item__request__researcher__last_name', 'status', 'request_item__request__request_date']
    serializer_class = RestrictedRequestsListSerializer