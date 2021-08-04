from rest_framework.generics import ListAPIView
from accession.models import Accession
from archival_unit.models import ArchivalUnit
from container.models import Container
from dashboard.serializers.log_serializers import AccessionLogSerializer, ArchivalUnitLogSerializer, IsadLogSerializer, \
    FindingAidsLogSerializer, DigitizationLogSerializer
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class AccessionLog(ListAPIView):
    queryset = Accession.objects.filter(transfer_date__isnull=False).order_by('-transfer_date', '-seq').all()[:20]
    serializer_class = AccessionLogSerializer
    pagination_class = None


class ArchivalUnitLog(ListAPIView):
    queryset = ArchivalUnit.objects.filter(date_created__isnull=False) \
        .order_by('-date_created', 'fonds', 'subfonds', 'series').all()[:20]
    serializer_class = ArchivalUnitLogSerializer
    pagination_class = None


class IsadCreateLog(ListAPIView):
    queryset = Isad.objects.filter(date_created__isnull=False) \
        .order_by('-date_created',).all()[:20]
    serializer_class = IsadLogSerializer
    pagination_class = None


class IsadUpdateLog(ListAPIView):
    queryset = Isad.objects.filter(date_updated__isnull=False) \
        .order_by('-date_updated',).all()[:20]
    serializer_class = IsadLogSerializer
    pagination_class = None


class FindingAidsCreateLog(ListAPIView):
    queryset = FindingAidsEntity.objects.filter(date_created__isnull=False) \
                   .order_by('-date_created', ).all()[:20]
    serializer_class = FindingAidsLogSerializer
    pagination_class = None


class FindingAidsUpdateLog(ListAPIView):
    queryset = FindingAidsEntity.objects.filter(date_updated__isnull=False) \
        .order_by('-date_updated',).all()[:20]
    serializer_class = FindingAidsLogSerializer
    pagination_class = None


class DigitizationLog(ListAPIView):
    queryset = Container.objects.filter(digital_version_creation_date__isnull=False) \
        .order_by('-digital_version_creation_date', 'archival_unit__reference_code', 'container_no').all()[:20]
    serializer_class = DigitizationLogSerializer
    pagination_class = None