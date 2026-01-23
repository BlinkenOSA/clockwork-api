from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.allowed_archival_unit_mixin import ListAllowedArchivalUnitMixin
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from clockwork_api.permissons.allowed_archival_unit_permission import AllowedArchivalUnitPermission
from isad.models import Isad
from isad.serializers.isad_serializers import IsadSelectSerializer, IsadReadSerializer, IsadWriteSerializer, IsadFondsSerializer, \
    IsadPreCreateSerializer
from django_filters import rest_framework as filters


class IsadFilterClass(filters.FilterSet):
    """
    Filter set for browsing the ISAD tree via fonds-level archival units.

    This filter set operates on :class:`archival_unit.models.ArchivalUnit`
    records (typically fonds-level units) and supports:
        - free-text search across fonds/subfonds/series titles
        - filtering by a derived "status" of ISAD existence/publication state

    The results are intended for the ISAD tree/list endpoint, where the root
    queryset is fonds-level archival units.
    """

    search = filters.CharFilter(label='Search', method='search_filter')
    status = filters.CharFilter(label='Status', method='filter_status')

    def search_filter(self, queryset, name, value):
        """
        Applies a free-text search across fonds/subfonds/series titles.

        Parameters
        ----------
        queryset : django.db.models.QuerySet
            Base archival unit queryset.
        name : str
            Filter field name (unused; required by django-filter signature).
        value : str
            Search value.

        Returns
        -------
        django.db.models.QuerySet
            Filtered queryset (distinct) matching the search term.
        """
        if value:
            return queryset.filter(
                (
                    Q(title__icontains=value) |
                    Q(children__title__icontains=value) |
                    Q(children__children__title__icontains=value)
                )
            ).distinct()

    def filter_status(self, queryset, name, value):
        """
        Filters archival units by derived ISAD existence/publication status.

        Supported values are matched by convention:

        - ``'not exists'``:
            Returns archival units where an ISAD record is missing at any level
            in the fonds/subfonds/series chain.
        - ``'draft'``:
            Returns archival units where an ISAD record exists but is not
            published at any level in the chain.
        - any other value:
            Returns archival units where an ISAD record is published at any
            level in the chain.

        Parameters
        ----------
        queryset : django.db.models.QuerySet
            Base archival unit queryset.
        name : str
            Filter field name (unused; required by django-filter signature).
        value : str
            Status selector.

        Returns
        -------
        django.db.models.QuerySet
            Filtered queryset (distinct) matching the requested status bucket.
        """
        if value == 'not exists':
            return queryset.filter(
                (
                        Q(isad__isnull=True) |
                        Q(children__isad__isnull=True) |
                        Q(children__children__isad__isnull=True)
                )
            ).distinct()
        elif value == 'draft':
            return queryset.filter(
                (
                        Q(isad__published=False) |
                        Q(children__isad__published=False) |
                        Q(children__children__isad__published=False)
                )
            ).distinct()
        else:
            return queryset.filter(
                (
                        Q(isad__published=True) |
                        Q(children__isad__published=True) |
                        Q(children__children__isad__published=True)
                )
            ).distinct()

    class Meta:
        model = ArchivalUnit
        fields = ('fonds',)


class IsadList(ListAllowedArchivalUnitMixin, generics.ListAPIView):
    """
    Lists fonds-level archival units for the ISAD tree view.

    The root queryset is fonds-level :class:`archival_unit.models.ArchivalUnit`
    objects (``level='F'``). The serialized output expands the archival unit
    structure via :class:`isad.serializers.isad_serializers.IsadFondsSerializer`.

    Filtering
    ---------
    Uses :class:`IsadFilterClass` via django-filter.

    Context
    -------
    Adds the current user to serializer context to support permission-aware
    child expansion in tree serializers.
    """

    queryset = ArchivalUnit.objects.filter(level='F').all()
    serializer_class = IsadFondsSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IsadFilterClass

    def get_serializer_context(self):
        """
        Extends serializer context with the requesting user.
        """
        context = super(IsadList, self).get_serializer_context()
        context['user'] = self.request.user
        return context


class IsadPreCreate(generics.RetrieveAPIView):
    """
    Returns prefill data for creating an ISAD record from an archival unit.

    Retrieves an :class:`archival_unit.models.ArchivalUnit` and serializes it
    into the minimal payload expected by ISAD creation workflows via
    :class:`isad.serializers.isad_serializers.IsadPreCreateSerializer`.
    """

    queryset = ArchivalUnit.objects.all()
    serializer_class = IsadPreCreateSerializer


class IsadCreate(AuditLogMixin, generics.CreateAPIView):
    """
    Creates a new ISAD record.

    Uses :class:`isad.serializers.isad_serializers.IsadWriteSerializer`, which
    supports nested writes for repeatable substructures.
    """

    queryset = Isad.objects.all()
    serializer_class = IsadWriteSerializer


class IsadDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single ISAD record.

    GET
        Returns a full ISAD record using :class:`IsadReadSerializer`, including
        nested read-only expansions for related substructures.

    PUT/PATCH
        Updates the ISAD record using :class:`IsadWriteSerializer`. Nested
        updates are supported where configured by the write serializer.

    DELETE
        Deletes the ISAD record.

    Permissions
    -----------
    Access is restricted by :class:`clockwork_api.permissons.allowed_archival_unit_permission.AllowedArchivalUnitPermission`.
    """

    permission_classes = [AllowedArchivalUnitPermission]
    queryset = Isad.objects.all()
    method_serializer_classes = {
        ('GET', ): IsadReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): IsadWriteSerializer
    }


class IsadPublish(APIView):
    """
    Publishes or unpublishes an ISAD record.

    The action is provided via the URL kwarg ``action`` and supports:
        - ``publish``: publishes the record
        - any other value: unpublishes the record
    """

    def put(self, request, *args, **kwargs):
        """
        Executes the publish/unpublish action for the requested ISAD record.
        """
        action = self.kwargs.get('action')
        isad_id = self.kwargs.get('pk')
        isad = get_object_or_404(Isad, pk=isad_id)

        if action == 'publish':
            isad.publish(request.user)
            return Response(status=status.HTTP_200_OK)
        else:
            isad.unpublish()
            return Response(status=status.HTTP_200_OK)


class IsadSelectList(generics.ListAPIView):
    """
    Returns a non-paginated list of ISAD records for selection/autocomplete UIs.

    Supports:
        - filtering by fonds/subfonds/series and description level
        - searching by reference code and title

    The queryset is ordered by fonds/subfonds/series to provide stable grouping.
    """

    serializer_class = IsadSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('archival_unit__fonds', 'archival_unit__subfonds', 'archival_unit__series', 'description_level',)
    search_fields = ('reference_code', 'title')
    queryset = Isad.objects.all().order_by('archival_unit__fonds', 'archival_unit__subfonds', 'archival_unit__series')
