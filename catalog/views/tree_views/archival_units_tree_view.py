from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from archival_unit.models import ArchivalUnit


class ArchivalUnitsTreeView(APIView):
    permission_classes = []

    def get_unit_data(self, archival_unit):
        data = {
            'id': archival_unit.id,
            'catalog_id': archival_unit.isad.catalog_id,
            'key': archival_unit.reference_code.replace(" ", "_").lower(),
            'title': archival_unit.title,
            'title_original': archival_unit.title_original,
            'reference_code': archival_unit.reference_code,
            'level': archival_unit.level,
            'themes': [theme.theme for theme in archival_unit.theme.all()],
            'children': []
        }
        return data

    def get(self, request, archival_unit_id):
        tree = []

        fonds = {}
        subfonds = {}
        actual_fond = 0
        actual_subfonds = 0

        if archival_unit_id == 'all':
            qs = ArchivalUnit.objects.filter(isad__published=True).select_related('isad').order_by('fonds', 'subfonds', 'series')
        else:
            archival_unit = get_object_or_404(ArchivalUnit, id=archival_unit_id)
            qs = ArchivalUnit.objects.filter(isad__published=True, fonds=archival_unit.fonds).order_by('fonds', 'subfonds', 'series')

        idx = 0
        for au in qs:
            idx += 1
            if au.level == 'F':
                if actual_fond != au.fonds:
                    if actual_fond != 0:
                        tree.append(fonds)
                fonds = self.get_unit_data(au)

            if au.level == 'SF':
                if au.subfonds != 0:
                    subfonds = self.get_unit_data(au)
                    if actual_subfonds != au.subfonds:
                        fonds['children'].append(subfonds)
                else:
                    subfonds = {'children': []}

            if au.level == 'S':
                series = self.get_unit_data(au)
                if au.subfonds == 0:
                    series['subfonds'] = False
                    fonds['children'].append(series)
                else:
                    series['subfonds'] = True
                    subfonds['children'].append(series)

            if idx == qs.count():
                tree.append(fonds)

            actual_fond = au.fonds
            actual_subfonds = au.subfonds

        return Response(tree)
