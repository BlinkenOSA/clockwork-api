from rest_framework import generics
from rest_framework.filters import SearchFilter

from research.models import ResearcherDegree
from research.serializers.researcher_degree_serializers import (
    ResearcherDegreeReadSerializer,
    ResearcherDegreeWriteSerializer,
    ResearcherDegreeSerializer,
)


class ResearcherDegreeList(generics.ListCreateAPIView):
    """
    Lists all researcher degrees or creates a new degree entry.

    GET:
        Returns all available researcher degrees ordered alphabetically
        using ResearcherDegreeReadSerializer.

    POST:
        Creates a new researcher degree using ResearcherDegreeWriteSerializer.

    Features:
        - Search support by degree name
        - Separate serializers for read and write operations
    """

    queryset = ResearcherDegree.objects.all().order_by('degree')
    filter_backends = (SearchFilter,)
    search_fields = ('degree',)
    method_serializer_classes = {
        ('GET', ): ResearcherDegreeReadSerializer,
        ('POST', ): ResearcherDegreeWriteSerializer
    }


class ResearcherDegreeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single researcher degree.

    GET:
        Returns full degree details using ResearcherDegreeReadSerializer.

    PUT/PATCH/DELETE:
        Updates or deletes the degree using ResearcherDegreeWriteSerializer.
    """

    queryset = ResearcherDegree.objects.all()
    method_serializer_classes = {
        ('GET', ): ResearcherDegreeReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ResearcherDegreeWriteSerializer
    }


class ResearcherDegreeSelectList(generics.ListAPIView):
    """
    Lightweight list of researcher degrees for selection components.

    Intended for dropdowns and autocomplete fields.

    Features:
        - Unpaginated output
        - Search by degree name
        - Minimal field set via ResearcherDegreeSerializer
    """

    serializer_class = ResearcherDegreeSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['degree']
    queryset = ResearcherDegree.objects.filter(show_in_registration_form=True).order_by('degree')
