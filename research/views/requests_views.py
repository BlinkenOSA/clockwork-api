import datetime
import json

import requests
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
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
    """
    FilterSet for research request items.

    Supports filtering by:
        - researcher (parent request's researcher)
        - request item status
        - item origin (Finding Aids / Library / Film Library)
        - request date buckets (today / next working day / next week)

    Notes:
        - Date buckets use the server's local date (``datetime.date.today()``).
        - ``next_day`` treats Friday–Sunday as "next Monday".
    """

    researcher = filters.CharFilter(label='Researcher', method='filter_researcher')
    status = filters.CharFilter(label='Status', method='filter_status')
    item_origin = filters.CharFilter(label='Item Origin', method='filter_item_origin')
    request_date = filters.CharFilter(label='Request Date', method='filter_request_date')

    def filter_researcher(self, queryset, name, value):
        """
        Filters request items by researcher identifier.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Researcher identifier (typically PK).

        Returns:
            A queryset filtered to request items belonging to the given researcher.
        """
        return queryset.filter(request__researcher=value)

    def filter_status(self, queryset, name, value):
        """
        Filters request items by workflow status.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Status value (e.g. '1', '2', '3', '4', '5', '9').

        Returns:
            A queryset filtered by the given status.
        """
        return queryset.filter(status=value)

    def filter_item_origin(self, queryset, name, value):
        """
        Filters request items by item origin.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Origin code (e.g. 'FA', 'L', 'FL').

        Returns:
            A queryset filtered by the given origin.
        """
        return queryset.filter(item_origin=value)

    def filter_request_date(self, queryset, name, value):
        """
        Filters request items by request date bucket.

        Supported values:
            - ``today``: request_date is today
            - ``all``: no filtering
            - ``next_day``: next working day (Mon–Thu -> +1 day; Fri–Sun -> next Monday)
            - ``next_week``: next Monday (inclusive) to the Monday after that (exclusive)

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Date bucket selector.

        Returns:
            A queryset filtered by the selected bucket.
        """
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
    """
    Lists research request items.

    Returns request items ordered by newest parent request first.

    Features:
        - Filtering via RequestFilterClass
        - Full-text search over researcher names, identifiers, titles, and barcodes
        - Ordering over operational workflow fields
    """

    queryset = RequestItem.objects.all().order_by('-request__created_date')
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = RequestFilterClass
    search_fields = [
        'request__researcher__last_name',
        'request__researcher__first_name',
        'container__archival_unit__reference_code',
        'identifier',
        'title',
        'container__barcode'
    ]
    ordering_fields = [
        'request__researcher__last_name',
        'status',
        'item_origin',
        'request__request_date',
        'ordering',
        'reshelve_date'
    ]
    serializer_class = RequestListSerializer


class RequestsCreate(CreateAPIView):
    """
    Creates a new research request with nested request items.

    POST:
        Creates a :class:`research.models.Request` and its related request items
        using :class:`research.serializers.requests_serializers.RequestCreateSerializer`.
    """

    serializer_class = RequestCreateSerializer
    queryset = Request.objects.all()


class RequestItemRetrieveUpdate(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single request item.

    GET:
        Uses RequestItemReadSerializer.

    PUT:
        Uses RequestItemWriteSerializer.

    Notes:
        PATCH is not explicitly mapped in method_serializer_classes and will
        fall back to default behavior.
    """

    method_serializer_classes = {
        ('GET', ): RequestItemReadSerializer,
        ('PUT', ): RequestItemWriteSerializer
    }
    queryset = RequestItem.objects.all()


class RequestsListForPrint(generics.ListAPIView):
    """
    Lists pending request items for printing.

    Returns all request items with status '2' (Pending) ordered by request date.
    Output is unpaginated.
    """

    serializer_class = RequestListSerializer
    pagination_class = None

    def get_queryset(self):
        """
        Builds the queryset of printable request items.

        Returns:
            A queryset of pending (status='2') request items ordered by request date.
        """
        return RequestItem.objects.filter(
            status='2'
        ).order_by('request__request_date')


class RequestItemStatusStep(APIView):
    """
    Advances or rewinds a request item's workflow status.

    PUT /requests/<action>/<request_item_id>/ where action is:
        - next: advance status (with special handling for digital versions)
        - previous: rewind status (only between 2..4)

    Side effects:
        - When advancing to status '3' (Processed and prepared) or '9' (Uploaded),
          sends a "delivered" email to the researcher.
        - When container has a digital version and current status is '2', the
          next step becomes '9' (Uploaded) instead of '3'.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the requested status transition.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing ``action`` and ``request_item_id``.

        Returns:
            200 OK on a successful transition.
        """
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
                        request_item.status = str(st + 1)
                        request_item.save()
            else:
                if st < 5:
                    request_item.status = str(st + 1)
                    request_item.save()

            # If delivered/uploaded, notify the researcher
            if request_item.status == '3' or request_item.status == '9':
                request_obj = request_item.request
                mail = EmailWithTemplate(
                    researcher=request_obj.researcher,
                    context={
                        'researcher': request_obj.researcher,
                        'request': request_obj,
                        'item': request_item
                    }
                )
                mail.send_request_delivered_user()

            return Response(status=status.HTTP_200_OK)

        if action == 'previous':
            if 1 < st < 5:
                request_item.status = str(st - 1)
                request_item.save()
            return Response(status=status.HTTP_200_OK)


class RequestSeriesSelect(generics.ListAPIView):
    """
    Selection endpoint for series-level archival units.

    Used by request creation UIs to select a series.

    Features:
        - Search by title_full
        - Dropdown-style pagination
    """

    queryset = ArchivalUnit.objects.filter(level='S').order_by('sort')
    filter_backends = [SearchFilter]
    search_fields = ['title_full']
    pagination_class = DropDownResultSetPagination
    serializer_class = ArchivalUnitSeriesSerializer


class RequestContainerSelect(generics.ListAPIView):
    """
    Selection endpoint for containers belonging to a given series.

    The series is provided by the ``series_id`` URL kwarg.

    Features:
        - Search by container_no
        - Dropdown-style pagination
    """

    filter_backends = [SearchFilter]
    search_fields = ['container_no']
    pagination_class = DropDownResultSetPagination
    serializer_class = ContainerListSerializer

    def get_queryset(self):
        """
        Returns the container queryset for the given series.

        Returns:
            Containers ordered by container number.
        """
        series_id = self.kwargs['series_id']
        return Container.objects.filter(archival_unit__id=series_id).order_by('container_no')


class RequestLibraryMLR(APIView):
    """
    Returns a combined collection/location string for a Koha library record.

    The view:
        - derives the Solr id from Koha id using Hashids
        - queries the "new catalog" Solr core
        - parses MARC JSON from the returned Solr document
        - extracts:
            - collections (MARC 580$a)
            - locations (MARC 952$c)

    Response rules:
        - If only collections exist: returns collections
        - If only locations exist: returns locations
        - If both exist: returns "<collections> / <locations>"
    """

    def get(self, request, *args, **kwargs):
        """
        Fetches MLR-like information for the given Koha record.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing ``koha_id``.

        Returns:
            A DRF Response with the combined string or an HTTP error status.
        """
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
            return Response(status=r.status_code)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def _get_locations(self, items):
        """
        Extracts distinct locations from MARC 952 fields.

        Args:
            items: MARC fields filtered to entries containing the ``952`` key.

        Returns:
            A set of location labels. Defaults to "General collection" when 952$c is missing.
        """
        locations = set()
        for item in items:
            subfields = list(filter(lambda sf: 'c' in sf, item['952']['subfields']))
            if subfields:
                locations.add(subfields[0]['c'])
            else:
                locations.add("General collection")
        return locations

    def _get_collections(self, fields):
        """
        Extracts distinct collection statements from MARC 580 fields.

        Args:
            fields: MARC fields filtered to entries containing the ``580`` key.

        Returns:
            A set of collection statement strings from 580$a.
        """
        collections = set()
        for field in fields:
            for sf in field['580']['subfields']:
                if 'a' in sf:
                    collections.add(sf['a'])
        return collections
