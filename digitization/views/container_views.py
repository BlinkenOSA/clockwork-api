from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from container.models import Container
from digitization.serializers.container_serializers import DigitizationContainerLogSerializer, \
    DigitizationContainerDataSerializer


class DigitizationContainerList(ListAPIView):
    filter_backends = (SearchFilter, OrderingFilter)
    ordering_fields = ('barcode', 'date_updated', 'digital_version_exists', 'digital_version_creation_date')
    search_fields = ('archival_unit__reference_code', 'barcode',
                     'findingaidsentity__title', 'findingaidsentity__title_original')
    serializer_class = DigitizationContainerLogSerializer

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

        digital_version = self.request.query_params.get('digital_version_exists', None)
        if digital_version == 'yes':
            qs = qs.filter(digital_version_exists=True)
        if digital_version == 'no':
            qs = qs.filter(digital_version_exists=False)

        digital_version_research_cloud = self.request.query_params.get('digital_version_research_cloud', None)
        if digital_version_research_cloud == 'yes':
            qs = qs.filter(digital_version_research_cloud=True)
        if digital_version_research_cloud == 'no':
            qs = qs.filter(digital_version_research_cloud=False)

        digital_version_online = self.request.query_params.get('digital_version_online', None)
        if digital_version_online == 'yes':
            qs = qs.filter(digital_version_online=True)
        if digital_version_online == 'no':
            qs = qs.filter(digital_version_online=False)

        return qs


class DigitizationContainerDetail(RetrieveAPIView):
    queryset = Container.objects.all()
    serializer_class = DigitizationContainerDataSerializer
