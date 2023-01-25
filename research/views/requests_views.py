from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from research.models import RequestItem
from research.serializers.requests_serializers import RequestListSerializer


class RequestsList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = RequestItem.objects.all().order_by('request__created_date')
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['request__researcher', 'status', 'item_origin', 'reshelve_date']
    ordering_fields = ['request__researcher__last_name', 'status', 'item_origin', 'request__request_date', 'request__created_date', 'reshelve_date']
    method_serializer_classes = {
        ('GET', ): RequestListSerializer,
    }


class RequestsListForPrint(generics.ListAPIView):
    serializer_class = RequestListSerializer
    pagination_class = None

    def get_queryset(self):
        return RequestItem.objects.filter(
            status='2'
        )

class RequestItemStatusStep(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        request_item_id = self.kwargs.get('request_item_id')
        request_item = get_object_or_404(RequestItem, pk=request_item_id)
        st = int(request_item.status)

        if action == 'next':
            if st < 4:
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
