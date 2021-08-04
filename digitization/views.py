from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from container.models import Container
from digitization.serializers import DigitizationLogSerializer, DigitizationDataSerializer


class DigitizationList(ListAPIView):
    filter_backends = (SearchFilter, OrderingFilter)
    ordering_fields = ('barcode', 'digital_version_exists', 'digital_version_creation_date')
    search_fields = ('archival_unit__reference_code', 'barcode',)
    serializer_class = DigitizationLogSerializer

    def get_queryset(self):
        qs = Container.objects.filter(barcode__isnull=False).exclude(barcode="").order_by('-digital_version_creation_date')

        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if 'container_no' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-archival_unit__fonds', '-archival_unit__subfonds', '-archival_unit__series', '-container_no')
                else:
                    qs = qs.order_by('archival_unit__fonds', 'archival_unit__subfonds', 'archival_unit__series', 'container_no')

            if 'carrier_type' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-carrier_type__type')
                else:
                    qs = qs.order_by('carrier_type__type')

        carrier_type = self.request.query_params.get('carrier_type', None)
        if carrier_type:
            qs = qs.filter(carrier_type=carrier_type)

        return qs


class DigitizationDetail(RetrieveAPIView):
    queryset = Container.objects.all()
    serializer_class = DigitizationDataSerializer
