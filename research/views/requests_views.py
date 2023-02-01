from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404, CreateAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSeriesSerializer
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from container.serializers import ContainerSelectSerializer
from research.models import RequestItem, Request
from research.serializers.requests_serializers import RequestListSerializer, ContainerListSerializer, \
    RequestWriteSerializer, RequestItemWriteSerializer


class RequestsList(generics.ListAPIView):
    queryset = RequestItem.objects.all().order_by('request__created_date')
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['request__researcher', 'status', 'item_origin', 'reshelve_date']
    ordering_fields = ['request__researcher__last_name', 'status', 'item_origin', 'request__request_date', 'request__created_date', 'reshelve_date']
    serializer_class = RequestListSerializer


class RequestsCreate(CreateAPIView):
    serializer_class = RequestWriteSerializer
    queryset = Request.objects.all()

    def perform_create(self, serializer):
        pass


class RequestsCreateBackup(APIView):
    def post(self, request, *args, **kwargs):
        # Create Request
        req = {
            'researcher': request.data.get('researcher', None),
            'request_date': request.data.get('request_date', None)
        }
        serializer = RequestWriteSerializer(data=req)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        req_record = serializer.instance

        # Create Request Item
        request_items = request.data.get('request_items', [])
        for request_item in request_items:
            request_item['request'] = req_record.id
            serializer = RequestItemWriteSerializer(data=request_item)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            req_item_record = serializer.instance
            if req_item_record.item_origin == 'FA':
                req_item_record.archival_unit = req_item_record.container.archival_unit.reference_code
                req_item_record.archival_reference_number = \
                    "%s:%s" % (req_item_record.container.archival_unit.reference_code,
                               req_item_record.container.container_no)
                req_item_record.save()

        return Response("OK", status=HTTP_200_OK)


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
            if st < 5:
                request_item.status = str(st+1)
                request_item.save()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_200_OK)
        if action == 'previous':
            if st > 1:
                request_item.status = str(st-1)
                request_item.save()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_200_OK)


class RequestSeriesSelect(generics.ListAPIView):
    queryset = ArchivalUnit.objects.filter(level='S').order_by('sort')
    filter_backends = [SearchFilter]
    search_fields = ['title_full']
    pagination_class = None
    serializer_class = ArchivalUnitSeriesSerializer


class RequestContainerSelect(generics.ListAPIView):
    filter_backends = [SearchFilter]
    search_fields = ['container_no']
    pagination_class = None
    serializer_class = ContainerListSerializer

    def get_queryset(self):
        series_id = self.kwargs['series_id']
        return Container.objects.filter(archival_unit__id=series_id).order_by('container_no')
