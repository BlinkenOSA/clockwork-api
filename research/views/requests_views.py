from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from research.models import RequestItem
from research.serializers.requests_serializers import RequestListSerializer
from research.serializers.researcher_serializers import ResearcherWriteSerializer, \
    ResearcherSelectSerializer, ResearcherListSerializer


class ResearcherRequestsList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = RequestItem.objects.all().order_by('-request__created_date')
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['researcher', 'status', 'item_origin', 'reshelve_date']
    ordering_fields = ['request__researcher__last_name', 'status', 'item_origin', 'request__date_created', 'reshelve_date']
    search_fields = ('first_name', 'last_name',)
    method_serializer_classes = {
        ('GET', ): RequestListSerializer,
    }
