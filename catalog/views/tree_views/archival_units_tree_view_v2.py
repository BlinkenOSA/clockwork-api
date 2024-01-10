from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from archival_unit.models import ArchivalUnit
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity


class ArchivalUnitsTreeViewV2(APIView):
    permission_classes = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.themes = {}

    def has_online_content(self, archival_unit):
        if archival_unit['level'] == 'F':
            fa_entity_set = FindingAidsEntity.objects.filter(
                archival_unit__parent__parent__id=archival_unit['id'],
                published=True
            )
            return DigitalVersion.objects.filter(
                finding_aids_entity__in=fa_entity_set,
                available_online=True
            ).count()
        if archival_unit['level'] == 'SF':
            fa_entity_set = FindingAidsEntity.objects.filter(
                archival_unit__parent__id=archival_unit['id'],
                published=True
            )
            return DigitalVersion.objects.filter(
                finding_aids_entity__in=fa_entity_set,
                available_online=True
            ).count()
        if archival_unit['level'] == 'S':
            return DigitalVersion.objects.filter(
                finding_aids_entity__in=archival_unit.findingaidsentity_set.all(),
                finding_aids_entity__published=True,
                available_online=True
            ).count()

    def get_unit_data(self, archival_unit):
        data = {
            'id': archival_unit['id'],
            'catalog_id': archival_unit['isad__catalog_id'],
            'key': archival_unit['reference_code'].replace(" ", "_").lower(),
            'title': archival_unit['title'],
            'title_original': archival_unit['title_original'],
            'reference_code': archival_unit['reference_code'],
            'level': archival_unit['level'],
            'themes': self.themes[archival_unit['id']],
            'children': []
        }
        return data

    def get_themes(self, qs):
        themes = {}
        for au in qs.values('id', 'theme'):
            if au['id'] in themes:
                themes[au['id']].append(au['theme'])
            else:
                themes[au['id']] = [au['theme']]
        self.themes = themes

    def get(self, request, archival_unit_id, theme):
        tree = []

        fonds = {}
        subfonds = {}
        actual_fond = 0
        actual_subfonds = 0

        if archival_unit_id == 'all':
            if theme and theme != 'all':
                qs = ArchivalUnit.objects.filter(
                    isad__published=True,
                    theme__id=theme
                ).select_related('isad').order_by('fonds', 'subfonds', 'series')
            else:
                qs = ArchivalUnit.objects.filter(isad__published=True).select_related('isad').order_by('fonds', 'subfonds', 'series')
        else:
            archival_unit = get_object_or_404(ArchivalUnit, id=archival_unit_id)
            qs = ArchivalUnit.objects.filter(isad__published=True, fonds=archival_unit.fonds).order_by('fonds', 'subfonds', 'series')

        qs = qs.values(
            'id', 'fonds', 'subfonds', 'series', 'reference_code', 'title', 'title_original', 'level',
            'isad__catalog_id'
        )

        # Get Themes
        self.get_themes(qs)

        idx = 0
        for au in qs:
            idx += 1
            if au['level'] == 'F':
                if actual_fond != au['fonds']:
                    if actual_fond != 0:
                        tree.append(fonds)
                fonds = self.get_unit_data(au)

            if au['level'] == 'SF':
                if au['subfonds'] != 0:
                    subfonds = self.get_unit_data(au)
                    if actual_subfonds != au['subfonds']:
                        fonds['children'].append(subfonds)
                else:
                    subfonds = {'children': []}

            if au['level'] == 'S':
                series = self.get_unit_data(au)
                if au['subfonds'] == 0:
                    series['subfonds'] = False
                    fonds['children'].append(series)
                else:
                    series['subfonds'] = True
                    subfonds['children'].append(series)

            if idx == qs.count():
                tree.append(fonds)

            actual_fond = au['fonds']
            actual_subfonds = au['subfonds']

        return Response(tree)
