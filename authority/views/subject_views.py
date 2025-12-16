from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Subject
from authority.serializers import SubjectSerializer, SubjectSelectSerializer


class SubjectList(generics.ListCreateAPIView):
    """
    Lists all subject authority records or creates a new one.

    GET:
        - Returns a searchable and orderable list of subject terms.

    POST:
        - Creates a new subject authority record.
    """

    queryset = Subject.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['subject']
    search_fields = ('subject',)
    serializer_class = SubjectSerializer


class SubjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single subject authority record.

    GET:
        - Returns full subject details.

    PUT / PATCH:
        - Updates the subject record.

    DELETE:
        - Deletes the subject record if not referenced elsewhere.
    """

    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class SubjectSelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of subjects for selection UIs.

    Features:
        - Alphabetical ordering
        - Searchable by subject label
        - Optimized for dropdowns and autocomplete widgets
    """

    serializer_class = SubjectSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('subject',)
    queryset = Subject.objects.all().order_by('subject')
