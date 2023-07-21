import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class NewlyAddedContent(APIView):
    permission_classes = []

    def get(self, *args, **kwargs):
        response = []
        if kwargs['content_type'] == 'isad':
            for isad in Isad.objects.filter(
                description_level='S',
                published=True
            ).order_by(
                '-date_published'
            ).all()[:5]:
                response.append({
                    'id': isad.catalog_id,
                    'reference_code': isad.reference_code,
                    'title': isad.archival_unit.title_full,
                    'date_published': isad.date_published
                })
        else:
            added_series = []
            for finding_aids in FindingAidsEntity.objects.select_related('archival_unit').filter(
                published=True,
                date_published__year__gt=datetime.datetime.now().year-2
            ).order_by(
                '-date_published'
            ).all():
                if len(added_series) == 5:
                    break
                if finding_aids.archival_unit.id not in added_series:
                    response.append({
                        'id': finding_aids.archival_unit.isad.catalog_id,
                        'reference_code': finding_aids.archival_unit.reference_code,
                        'title': finding_aids.archival_unit.title_full,
                        'date_published': finding_aids.date_published
                    })
                    added_series.append(finding_aids.archival_unit.id)
        return Response(response)
