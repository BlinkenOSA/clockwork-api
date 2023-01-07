from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity


class FindingAidsEntityLocationView(APIView):
    permission_classes = []

    def get_archival_unit_data(self, archival_unit):
        return {
            'id': archival_unit.id,
            'catalog_id': archival_unit.isad.catalog_id,
            'key': archival_unit.reference_code.replace(" ", "_").lower(),
            'title': archival_unit.title,
            'title_original': archival_unit.title_original,
            'reference_code': archival_unit.reference_code,
            'level': archival_unit.level,
            'has_subfonds': archival_unit.subfonds != 0,
            'children': []
        }

    def get_placeholder(self, level, has_subfonds):
        return {
            'key': 'placeholder',
            'level': level,
            'has_subfonds': has_subfonds
        }

    def get_container_data(self, container):
        return {
            'key': "%s_%s" % (container.archival_unit.reference_code.replace(" ", "_").lower(), container.container_no),
            'reference_code': "%s:%s" % (container.archival_unit.reference_code, container.container_no),
            'container_no': container.container_no,
            'level': 'container',
            'carrier_type': container.carrier_type.type,
            'has_subfonds': container.archival_unit.subfonds != 0,
        }

    def get_fa_entity_data(self, fa_entity, active=False):
        return {
            'catalog_id': fa_entity.catalog_id,
            'key': fa_entity.archival_reference_code.replace(" ", "_").lower(),
            'reference_code': fa_entity.archival_reference_code,
            'title': fa_entity.title,
            'active': active,
            'level': 'folder' if fa_entity.level == 'F' else 'item',
            'has_subfonds': fa_entity.archival_unit.subfonds != 0,
        }

    def get(self, request, fa_entity_catalog_id):
        tree = []

        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=fa_entity_catalog_id, archival_unit__isad__published=True)
        series = fa_entity.archival_unit
        subfonds = series.parent
        fonds = subfonds.parent
        container = fa_entity.container

        if hasattr(fonds, 'isad'):
            tree.append(self.get_archival_unit_data(fonds))

        if hasattr(subfonds, 'isad'):
            tree.append(self.get_archival_unit_data(subfonds))

        if hasattr(series, 'isad'):
            tree.append(self.get_archival_unit_data(series))

        # Add active container
        tree.append(self.get_container_data(container))

        # L1 description level
        if fa_entity.description_level == 'L1':

            # Finding Aids Entities
            fa_qs = FindingAidsEntity.objects.filter(container=container).order_by('folder_no', 'sequence_no')
            fa_count = fa_qs.count()
            fa_first = fa_qs.first()
            fa_last = fa_qs.last()

            # Add first FA Entity in container
            tree.append(self.get_fa_entity_data(fa_first, fa_first.archival_reference_code == fa_entity.archival_reference_code))

            # Add placeholder
            if fa_entity.folder_no > 3:
                tree.append(self.get_placeholder('folder', fa_entity.archival_unit.subfonds != 0))

            # Add previous
            if fa_entity.folder_no > 2:
                fa_previous = fa_qs.filter(folder_no=fa_entity.folder_no-1).first()
                tree.append(self.get_fa_entity_data(fa_previous, False))

            # Add active
            if container.container_no == fa_entity.container.container_no and \
               fa_first.archival_reference_code != fa_entity.archival_reference_code and \
               fa_last.archival_reference_code != fa_entity.archival_reference_code:
                tree.append(self.get_fa_entity_data(fa_entity, True))

            # Add next
            if fa_entity.folder_no + 1 < fa_count:
                fa_next = fa_qs.filter(folder_no=fa_entity.folder_no+1).first()
                tree.append(self.get_fa_entity_data(fa_next, False))

            # Add placeholder
            if fa_entity.folder_no + 2 < fa_count:
                tree.append(self.get_placeholder('folder', fa_entity.archival_unit.subfonds != 0))

            # Add last
            if fa_count > 1:
                tree.append(self.get_fa_entity_data(fa_last, fa_last.archival_reference_code == fa_entity.archival_reference_code))

        return Response(tree)
