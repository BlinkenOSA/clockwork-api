from typing import Type

from django.db.models import Count, F, QuerySet
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Person
from authority.serializers import PersonSerializer, PersonSelectSerializer, PersonListSerializer


class PersonList(generics.ListCreateAPIView):
    """
    Lists person authority records or creates a new person.

    GET:
        - Returns a list optimized for administrative and authority-management UIs.
        - Includes computed usage counts derived from finding aids:
            * fa_subject_count
            * fa_associated_count
            * fa_total_count
        - Supports searching across:
            * first and last names
            * alternative name formats
        - Supports custom ordering by:
            * name
            * usage counts

    POST:
        - Creates a new person authority record.
        - Uses the full PersonSerializer to support nested writes.
    """

    queryset = Person.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['last_name', 'last_name', 'fa_subject_count', 'fa_associated_count', 'fa_total_count']
    search_fields = ('first_name', 'last_name', 'personotherformat__first_name', 'personotherformat__last_name')

    def get_serializer_class(self) -> Type[PersonSerializer | PersonListSerializer]:
        """
        Selects serializer dynamically based on HTTP method.

        Returns:
            - PersonSerializer for POST (full create/update support)
            - PersonListSerializer for GET (optimized list representation)
        """

        if self.request.method == 'POST':
            return PersonSerializer
        else:
            return PersonListSerializer

    def get_queryset(self) -> QuerySet[Person]:
        """
        Returns a queryset annotated with finding-aids usage counts.

        Annotations:
            fa_subject_count:
                Number of finding aids where the person appears as a subject.

            fa_associated_count:
                Number of finding aids where the person appears as an
                associated person.

            fa_total_count:
                Sum of subject and associated usage counts.

        Ordering:
            - Supports ordering by computed name ("name")
            - Supports ordering by usage counts
            - Falls back to default queryset ordering
        """

        qs = Person.objects.annotate(
            fa_subject_count=Count('subject_poeple', distinct=True),
            fa_associated_count=Count(
                'findingaidsentityassociatedperson__fa_entity',
                distinct=True,
            ),
        ).annotate(
            fa_total_count=F('fa_subject_count') + F('fa_associated_count')
        )

        ordering = self.request.query_params.get('ordering')

        # Name ordering
        if ordering == 'name':
            return qs.order_by('last_name', 'first_name')
        elif ordering == '-name':
            return qs.order_by('-last_name', '-first_name')

        if ordering == 'fa_total_count':
            return qs.order_by('fa_total_count', 'last_name', 'first_name')
        elif ordering == '-name':
            return qs.order_by('-fa_total_count', 'last_name', 'first_name')

        return qs


class PersonDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single person authority record.

    GET:
        - Returns full person details, including alternative name formats.

    PUT / PATCH:
        - Updates the person and nested alternative formats.

    DELETE:
        - Deletes the person record if not referenced elsewhere.
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class PersonSelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of persons for selection UIs.

    Features:
        - Alphabetical ordering by last name, then first name
        - Searchable by:
            * primary names
            * alternative name formats
        - Optimized for dropdowns and autocomplete widgets
    """

    serializer_class = PersonSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('last_name', 'first_name', 'personotherformat__first_name', 'personotherformat__last_name')
    queryset = Person.objects.all().order_by('last_name', 'first_name')
