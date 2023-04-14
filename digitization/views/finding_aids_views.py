from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from digitization.serializers.finding_aids_serializers import FindingAidsEntityLogSerializer, \
    FindingAidsEntityDataSerializer
from finding_aids.models import FindingAidsEntity


class DigitizationFindingAidsList(ListAPIView):
    filter_backends = (SearchFilter, OrderingFilter)
    ordering_fields = ('archival_reference_code', 'digital_version_exists', 'digital_version_creation_date',
                       'primary_type')
    search_fields = ('archival_reference_code', 'title',)
    serializer_class = FindingAidsEntityLogSerializer

    def get_queryset(self):
        qs = FindingAidsEntity.objects.filter(digital_version_exists=True).order_by('-digital_version_creation_date')

        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if 'archival_reference_code' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-archival_unit__fonds', '-archival_unit__subfonds', '-archival_unit__series',
                                     '-container__container_no', 'sequence_no')
                else:
                    qs = qs.order_by('archival_unit__fonds', 'archival_unit__subfonds', 'archival_unit__series',
                                     'container__container_no', 'sequence_no')

            if 'primary_type' in ordering:
                if "-" in ordering:
                    qs = qs.order_by('-primary_type__type')
                else:
                    qs = qs.order_by('primary_type__type')

        primary_type = self.request.query_params.get('primary_type', None)
        if primary_type:
            qs = qs.filter(primary_type=primary_type)

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


class DigitizationFindingAidsDetail(RetrieveAPIView):
    queryset = FindingAidsEntity.objects.all()
    serializer_class = FindingAidsEntityDataSerializer
