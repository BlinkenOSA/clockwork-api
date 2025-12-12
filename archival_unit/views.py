from django.db.models import QuerySet
from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSelectSerializer, ArchivalUnitReadSerializer, \
    ArchivalUnitWriteSerializer, ArchivalUnitFondsSerializer, ArchivalUnitSeriesSerializer, \
    ArchivalUnitPreCreateSerializer
from clockwork_api.mixins.allowed_archival_unit_mixin import ListAllowedArchivalUnitMixin
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin


class ArchivalUnitFilterClass(filters.FilterSet):
    """
    FilterSet for fonds-level archival units.

    Allows searching across:
        - fonds titles
        - child subfonds titles
        - grandchild series titles

    Search is restricted to units with level == 'F'.
    """
    search = filters.CharFilter(label='Search', method='search_filter')

    def search_filter(
            self,
            queryset: QuerySet[ArchivalUnit],
            name: str,
            value: str
    ) -> QuerySet[ArchivalUnit]:
        """
        Performs a deep search across the first three hierarchical levels.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Search string.

        Returns:
            A distinct queryset of fonds units matching the search.
        """
        return ArchivalUnit.objects.filter(
            (
                Q(title__icontains=value) |
                Q(children__title__icontains=value) |
                Q(children__children__title__icontains=value)
            ) & Q(level='F')
        ).distinct()

    class Meta:
        model = ArchivalUnit
        fields = ('fonds',)


class ArchivalUnitPreCreate(generics.RetrieveAPIView):
    """
    Retrieves pre-populated metadata required for creating a child archival unit.

    Uses ArchivalUnitPreCreateSerializer to determine:
        - Next hierarchical level (F → SF, SF → S)
        - Relevant title/acronym metadata
    """
    queryset = ArchivalUnit.objects.all()
    serializer_class = ArchivalUnitPreCreateSerializer


class ArchivalUnitList(AuditLogMixin, MethodSerializerMixin, generics.ListCreateAPIView):
    """
    Lists all fonds-level archival units or creates a new fonds unit.

    GET:
        Returns a hierarchical list of fonds with nested children using
        ArchivalUnitFondsSerializer.

    POST:
        Creates a new archival unit using ArchivalUnitWriteSerializer.

    Features:
        - Audit logging
        - Dynamic serializer selection based on HTTP method
        - Filtering support (fonds-level only)
    """
    queryset = ArchivalUnit.objects.filter(level='F')
    method_serializer_classes = {
        ('GET', ): ArchivalUnitFondsSerializer,
        ('POST', ): ArchivalUnitWriteSerializer
    }
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ArchivalUnitFilterClass


class ArchivalUnitDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single archival unit.

    GET:
        Uses ArchivalUnitReadSerializer for full display.

    PUT/PATCH/DELETE:
        Uses ArchivalUnitWriteSerializer for write operations.
    """
    queryset = ArchivalUnit.objects.all()
    method_serializer_classes = {
        ('GET', ): ArchivalUnitReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ArchivalUnitWriteSerializer
    }


class ArchivalUnitSelectList(ListAllowedArchivalUnitMixin, generics.ListAPIView):
    """
    Lightweight list of archival units for dropdown/select UI components.

    Features:
        - Access control via ListAllowedArchivalUnitMixin
        - Searching by title or reference code
        - Filtering by hierarchical identifiers
        - Unpaginated output
    """
    serializer_class = ArchivalUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('fonds', 'subfonds', 'series', 'level', 'parent')
    search_fields = ['title', 'reference_code']
    queryset = ArchivalUnit.objects.all().order_by('fonds', 'subfonds', 'series')


class ArchivalUnitSelectByParentList(generics.ListAPIView):
    """
    Returns archival units whose parent matches the provided unit.

    Access control:
        - If the user has assigned archival units, only units within their
          allowed scope are returned.
        - Otherwise, returns all children of the specified parent.
        - If no parent_id is provided, returns an empty set.

    This is used for hierarchical dropdowns where the available children are
    filtered based on both parent ID and user permissions.
    """
    serializer_class = ArchivalUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ['title', 'reference_code']

    def get_queryset(self) -> QuerySet[ArchivalUnit]:
        """
        Builds the queryset dynamically based on:
            - The requested parent archival unit
            - The user's allowed archival units (if any)

        Returns:
            A filtered queryset of permitted children.
        """
        parent_id = self.kwargs.get('parent_id', None)
        user = self.request.user

        # If the user has assigned archival units, apply restrictions
        allowed_qs = user.user_profile.allowed_archival_units.all()

        if allowed_qs.exists():
            parent_unit = ArchivalUnit.objects.get(pk=parent_id)

            # Fonds → return subfonds and only those permitted
            if parent_unit.level == "F":
                subfonds_qs = ArchivalUnit.objects.filter(parent_id=parent_id)
                allowed_parents = ArchivalUnit.objects.filter(
                    id__in=allowed_qs.values_list("parent_id", flat=True)
                )
                return allowed_parents & subfonds_qs

            # Subfonds → return permitted series
            if parent_unit.level == "SF":
                series_qs = ArchivalUnit.objects.filter(parent_id=parent_id)
                return series_qs & allowed_qs

        # If the user has no restrictions
        if parent_id:
            return ArchivalUnit.objects.filter(parent_id=parent_id)

        return ArchivalUnit.objects.none()