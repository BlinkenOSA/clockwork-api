from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from container.models import Container
from digitization.models import DigitalVersion
from digitization.serializers.container_serializers import DigitizationContainerLogSerializer, \
    DigitizationContainerDataSerializer


class DigitizationContainerList(ListAPIView):
    """
    Lists containers for digitization workflows.

    This endpoint is used by the Archival Management System to browse and filter
    containers with barcodes, along with their digitization status.

    Search behavior:
        - Uses DRF SearchFilter
        - Searches over:
            - archival_unit__reference_code
            - barcode
            - findingaidsentity__title
            - findingaidsentity__title_original

    Ordering behavior:
        - Supports DRF ordering by:
            - barcode
            - date_updated
            - digital_version_exists
            - digital_version_creation_date
        - Provides custom ordering for:
            - container_no (orders by archival unit hierarchy + container number)
            - carrier_type (orders by carrier_type__type)

    Filtering behavior:
        - carrier_type: exact match
        - digital_version_exists: 'yes' / 'no'
        - digital_version_research_cloud: 'yes' / 'no'
        - digital_version_online: 'yes' / 'no'
    """

    filter_backends = (SearchFilter, OrderingFilter)
    ordering_fields = ('creation_date')
    search_fields = ('container__archival_unit__reference_code', 'container__barcode')
    serializer_class = DigitizationContainerLogSerializer

    def get_queryset(self):
        """
        Builds a filtered and ordered queryset of digitization-relevant containers.

        Base queryset:
            - includes only containers with non-empty barcodes
            - ordered by most recent digital version creation date

        Custom ordering:
            - ordering contains 'container_no' -> hierarchical ordering by fonds/subfonds/series + container_no
            - ordering contains 'carrier_type' -> ordering by carrier_type__type

        Query parameters:
            - ordering
            - carrier_type
            - digital_version_exists ('yes'/'no')
            - digital_version_research_cloud ('yes'/'no')
            - digital_version_online ('yes'/'no')
        """
        qs = DigitalVersion.objects.filter(
            container__isnull=False,
            finding_aids_entity__isnull=True,
            level='A'
        ).order_by(
            '-creation_date',
            'container__archival_unit__fonds',
            'container__archival_unit__subfonds',
            'container__archival_unit__series',
            'container__container_no'
        )

        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if 'container_no' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-container__archival_unit__fonds', '-container__archival_unit__subfonds', '-container__archival_unit__series', '-container__container_no')
                else:
                    qs = qs.order_by('container__archival_unit__fonds', 'container__archival_unit__subfonds', 'container__archival_unit__series', 'container__container_no')

            if 'carrier_type' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-container__carrier_type__type')
                else:
                    qs = qs.order_by('container__carrier_type__type')

            if 'barcode' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-container__barcode')
                else:
                    qs = qs.order_by('container__barcode')

        carrier_type = self.request.query_params.get('carrier_type', None)
        if carrier_type:
            qs = qs.filter(container__carrier_type=carrier_type)

        digital_version_online = self.request.query_params.get('digital_version_online', None)
        if digital_version_online == 'yes':
            qs = qs.filter(available_online=True)
        if digital_version_online == 'no':
            qs = qs.filter(available_online=False)

        digital_version_research_cloud = self.request.query_params.get('digital_version_research_cloud', None)
        if digital_version_research_cloud == 'yes':
            qs = qs.filter(available_research_cloud=True)
        if digital_version_research_cloud == 'no':
            qs = qs.filter(available_research_cloud=False)

        return qs


class DigitizationContainerDetail(RetrieveAPIView):
    """
    Retrieves container digitization metadata for detail views.

    This endpoint returns a container's parsed technical metadata using the
    DigitizationContainerDataSerializer.
    """

    queryset = DigitalVersion.objects.all()
    serializer_class = DigitizationContainerDataSerializer
