from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from isaar.models import Isaar, IsaarRelationship, IsaarPlaceQualifier
from isaar.serializers import IsaarSelectSerializer, IsaarReadSerializer, IsaarWriteSerializer, IsaarListSerializer, \
    IsaarRelationshipSerializer, IsaarPlaceQualifierSerializer


class IsaarList(AuditLogMixin, MethodSerializerMixin, generics.ListCreateAPIView):
    """
    Lists ISAAR records and supports creating new records.

    GET
        Returns a paginated list of ISAAR authority records using
        :class:`isaar.serializers.IsaarListSerializer`.

        Supports:
            - full-text search on ``name``
            - filtering by ``type`` and ``status``
            - ordering by ``name``, ``type``, ``status``

    POST
        Creates a new ISAAR record using :class:`isaar.serializers.IsaarWriteSerializer`.

        The write serializer supports nested writes for related names,
        identifiers, and places.
    """

    queryset = Isaar.objects.all()
    method_serializer_classes = {
        ('GET', ): IsaarListSerializer,
        ('POST', ): IsaarWriteSerializer
    }
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    ordering_fields = ('name', 'type', 'status')
    filterset_fields = ('type', 'status')
    search_fields = ('name',)


class IsaarDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single ISAAR record.

    GET
        Returns a full ISAAR record using :class:`isaar.serializers.IsaarReadSerializer`,
        including nested read-only expansions for related names, identifiers, and places.

    PUT/PATCH
        Updates an ISAAR record using :class:`isaar.serializers.IsaarWriteSerializer`.
        Nested updates are supported where configured by the write serializer.

    DELETE
        Deletes an ISAAR record.
    """

    queryset = Isaar.objects.all()
    method_serializer_classes = {
        ('GET', ): IsaarReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): IsaarWriteSerializer
    }


class IsaarSelectList(generics.ListAPIView):
    """
    Returns a non-paginated list of ISAAR records for selection UIs.

    Intended for dropdowns/autocomplete. Uses :class:`isaar.serializers.IsaarSelectSerializer`
    and disables pagination.

    Supports:
        - filtering by ``type``
        - searching by ``name``
    """

    serializer_class = IsaarSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('type',)
    search_fields = ('name',)
    queryset = Isaar.objects.all().order_by('name')


class IsaarRelationshipSelectList(generics.ListAPIView):
    """
    Returns a non-paginated list of ISAAR relationship terms.

    Intended for selection UIs when choosing a relationship qualifier for
    :class:`isaar.models.IsaarOtherName`.

    Notes
    -----
    The configured ``search_fields`` uses ``'theme'`` which does not correspond
    to a field on :class:`isaar.models.IsaarRelationship` (which has
    ``relationship``). If search is expected to work, this likely should be
    updated to ``('relationship',)``.
    """

    serializer_class = IsaarRelationshipSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('theme',)
    queryset = IsaarRelationship.objects.all().order_by('relationship')


class IsaarPlaceQualifierSelectList(generics.ListAPIView):
    """
    Returns a non-paginated list of ISAAR place qualifier terms.

    Intended for selection UIs when choosing a qualifier for an ISAAR place
    association.

    Notes
    -----
    The configured ``search_fields`` uses ``'place'`` which does not correspond
    to a field on :class:`isaar.models.IsaarPlaceQualifier` (which has
    ``qualifier``). If search is expected to work, this likely should be updated
    to ``('qualifier',)``.
    """

    serializer_class = IsaarPlaceQualifierSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('place',)
    queryset = IsaarPlaceQualifier.objects.all().order_by('qualifier')
