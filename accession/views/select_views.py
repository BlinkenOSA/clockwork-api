from rest_framework import generics

from accession.models import AccessionMethod, AccessionCopyrightStatus
from accession.serializers import AccessionMethodSelectSerializer, AccessionCopyrightStatusSelectSerializer


class AccessionMethodSelectList(generics.ListAPIView):
    """
    Returns an unpaginated list of all accession methods.

    This endpoint is intended for select/dropdown widgets where the full list
    of available accession methods is needed. Results are ordered
    alphabetically by the `method` field.
    """
    pagination_class = None
    serializer_class = AccessionMethodSelectSerializer
    queryset = AccessionMethod.objects.all().order_by('method')


class AccessionCopyrightStatusSelectList(generics.ListAPIView):
    """
    Returns an unpaginated list of all copyright status options.

    Used by UI components that require a full controlled vocabulary list.
    Results are ordered alphabetically by the `status` field.
    """
    pagination_class = None
    serializer_class = AccessionCopyrightStatusSelectSerializer
    queryset = AccessionCopyrightStatus.objects.all().order_by('status')
