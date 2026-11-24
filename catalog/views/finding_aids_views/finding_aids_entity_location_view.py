"""
Finding aids entity location view for the public catalog.

This module exposes a read-only endpoint that constructs a hierarchical
"context tree" showing where a finding aids entity lives within the
archival structure.

The response is designed specifically for frontend navigation widgets
(e.g. breadcrumbs, tree previews, location context panels), not for
generic data access.

Key characteristics:
    - Read-only
    - Public
    - Highly UI-oriented
    - Returns a partially-expanded tree centered on the active entity
"""
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity


class FindingAidsEntityLocationView(APIView):
    """
    Returns a hierarchical location tree for a finding aids entity.

    This view builds a minimal navigation tree showing:
        - Fonds
        - Subfonds
        - Series
        - Container
        - Nearby folders/items

    The tree is intentionally partial and optimized for UI context:
        - Only the relevant branch is expanded
        - Placeholder nodes are used to indicate omitted siblings
        - The active entity is highlighted

    This endpoint should not be treated as a general-purpose tree API.
    """

    permission_classes = []

    def get_archival_unit_data(self, archival_unit: ArchivalUnit) -> dict:
        """
        Serializes an archival unit into a tree node structure.

        This representation is optimized for frontend navigation and
        differs from full archival unit serializers.

        Returns:
            Dictionary representing an archival unit tree node.
        """

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

    def get_placeholder(self, level: str, has_subfonds: bool):
        """
        Returns a placeholder node representing omitted siblings.

        Placeholders are used by the frontend to visually indicate
        that additional nodes exist but are not expanded.

        Args:
            level:
                Logical level of omitted nodes (e.g. "folder").

            has_subfonds:
                Whether the owning archival unit has subfonds.
        """

        return {
            'key': 'placeholder',
            'level': level,
            'has_subfonds': has_subfonds
        }

    def get_container_data(self, container: Container) -> dict:
        """
        Serializes a container into a tree node.

        Containers represent the physical grouping level between
        archival units and finding aids entities.
        """

        return {
            'key': "%s_%s" % (container.archival_unit.reference_code.replace(" ", "_").lower(), container.container_no),
            'reference_code': "%s:%s" % (container.archival_unit.reference_code, container.container_no),
            'container_no': container.container_no,
            'level': 'container',
            'carrier_type': container.carrier_type.type,
            'has_subfonds': container.archival_unit.subfonds != 0,
        }

    def get_fa_entity_data(self, fa_entity: FindingAidsEntity, active: bool = False):
        """
        Serializes a finding aids entity into a tree node.

        Args:
            fa_entity:
                FindingAidsEntity instance.

            active:
                Whether this entity is the currently viewed entity.

        Returns:
            Dictionary representing a folder/item node.
        """

        return {
            'catalog_id': fa_entity.catalog_id,
            'key': fa_entity.archival_reference_code.replace(" ", "_").lower(),
            'reference_code': fa_entity.archival_reference_code,
            'title': fa_entity.title,
            'active': active,
            'level': 'folder' if fa_entity.level == 'F' else 'item',
            'has_subfonds': fa_entity.archival_unit.subfonds != 0,
        }

    def get(self, request, fa_entity_catalog_id: str):
        """
        Builds and returns a contextual location tree for a finding aids entity.

        The tree is centered on the active entity and includes:
            - archival hierarchy above it
            - container level
            - selected sibling folders/items

        The logic intentionally limits how many siblings are shown
        to keep the UI responsive and readable.
        """

        tree = []

        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=fa_entity_catalog_id, archival_unit__isad__published=True)

        # Resolve hierarchy
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

        # Folder level context
        if fa_entity.description_level == 'L1':

            # Use existing top-level siblings: folder numbers may contain gaps
            # or start above 1, and L2 items belong beneath their folders.
            fa_qs = FindingAidsEntity.objects.filter(
                container=container, description_level='L1'
            ).order_by('folder_no', 'sequence_no')
            fa_first = fa_qs.first()
            fa_last = fa_qs.last()
            previous = list(fa_qs.filter(folder_no__lt=fa_entity.folder_no)
                            .order_by('-folder_no', '-sequence_no')[:2])
            following = list(fa_qs.filter(folder_no__gt=fa_entity.folder_no)[:2])

            if previous:
                tree.append(self.get_fa_entity_data(fa_first))

                # A second preceding sibling beyond the first means some
                # records are omitted between the first and previous nodes.
                if len(previous) > 1 and previous[1].catalog_id != fa_first.catalog_id:
                    tree.append(self.get_placeholder('folder', series.subfonds != 0))

                if previous[0].catalog_id != fa_first.catalog_id:
                    tree.append(self.get_fa_entity_data(previous[0]))

            tree.append(self.get_fa_entity_data(fa_entity, True))

            if following:
                if following[0].catalog_id != fa_last.catalog_id:
                    tree.append(self.get_fa_entity_data(following[0]))

                if len(following) > 1 and following[1].catalog_id != fa_last.catalog_id:
                    tree.append(self.get_placeholder('folder', series.subfonds != 0))

                tree.append(self.get_fa_entity_data(fa_last))

        return Response(tree)
