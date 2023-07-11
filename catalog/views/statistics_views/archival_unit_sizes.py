from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity


class ArchivalUnitSizes(APIView):
    def get(self, *args, **kwargs):
        archival_unit_sizes = []
        for archival_unit in ArchivalUnit.objects.filter(
            level='F',
            isad__published=True
        ).all():
            au = {}
            au['reference_code'] = archival_unit.reference_code
            au['title'] = archival_unit.title
            au['size'] = FindingAidsEntity.objects.filter(
                archival_unit__parent__parent=archival_unit,
                published=True
            ).count()
            archival_unit_sizes.append(au)
        return Response(archival_unit_sizes)