"""
Full archival units tree view for the public catalog.

This module provides a read-only endpoint that constructs a hierarchical
tree of archival units (fonds → subfonds → series) for catalog navigation.

The tree is optimized for:
    - frontend browsing and exploration
    - thematic filtering
    - efficient hierarchical rendering

Important characteristics:
    - Only published ISAD records are included
    - The tree is built from denormalized querysets
    - Logic is intentionally UI-driven, not domain-driven
    - This endpoint is NOT a generic archival hierarchy API
"""
from django.db.models import QuerySet
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from archival_unit.models import ArchivalUnit
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity


class ArchivalUnitsTreeView(APIView):
    """
    Returns a full hierarchical tree of archival units.

    This view constructs a fonds → subfonds → series tree suitable
    for public catalog navigation.

    Supported modes:
        - Full tree ("all")
        - Tree scoped to a specific fonds
        - Tree filtered by thematic tag

    Design notes:
        - Tree nodes are constructed manually for performance
        - ArchivalUnit objects are accessed via values() queries
        - Children are assembled incrementally in a single pass
    """

    permission_classes = []

    def __init__(self, **kwargs):
        """
        Initializes per-request theme storage.

        Themes are preloaded and cached to avoid repeated lookups
        while building the tree.
        """
        super().__init__(**kwargs)
        self.themes = {}

    def has_online_content(self, archival_unit: dict) -> int:
        """
        Returns the number of online digital objects under an archival unit.

        This helper inspects descendant finding aids entities and counts
        associated digital versions marked as available online.

        Args:
            archival_unit:
                Dictionary representation of an archival unit node.

        Returns:
            Count of available online digital versions.

        Note:
            This method is currently unused in the tree output but
            exists for potential UI indicators (e.g. online badges).
        """
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

    def get_unit_data(self, archival_unit: dict) -> dict:
        """
        Serializes an archival unit dictionary into a tree node.

        The output structure is designed specifically for frontend
        tree components and differs from generic serializers.

        Args:
            archival_unit:
                Dictionary from values() queryset.

        Returns:
            Dictionary representing a tree node.
        """
        return {
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

    def get_themes(self, qs: QuerySet):
        """
        Preloads thematic tags for archival units in the queryset.

        Themes are stored in a dictionary keyed by archival unit ID
        to allow O(1) access during tree construction.

        Args:
            qs:
                Values queryset containing archival unit IDs and themes.
        """
        themes = {}
        for au in qs.values('id', 'theme'):
            if au['id'] in themes:
                themes[au['id']].append(au['theme'])
            else:
                themes[au['id']] = [au['theme']]
        self.themes = themes

    def get(self, request, archival_unit_id: str, theme: str) -> Response:
        """
        Builds and returns the archival units tree.

        Args:
            archival_unit_id:
                Either:
                    - "all" for the complete tree
                    - an archival unit ID to scope the tree to a fonds

            theme:
                Optional theme identifier used to filter archival units.

        Returns:
            JSON response containing a hierarchical tree structure.
        """
        tree = []

        fonds = {}
        subfonds = {}
        actual_fond = 0
        actual_subfonds = 0

        # Query selection logic
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

        # Denormalize queryset for tree construction
        qs = qs.values(
            'id', 'fonds', 'subfonds', 'series', 'reference_code', 'title', 'title_original', 'level',
            'isad__catalog_id'
        )

        # Get Themes
        self.get_themes(qs)

        idx = 0
        for au in qs:
            idx += 1

            # Hierarchy assembly
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

            # Finalize tree
            if idx == qs.count():
                tree.append(fonds)

            actual_fond = au['fonds']
            actual_subfonds = au['subfonds']

        return Response(tree)
