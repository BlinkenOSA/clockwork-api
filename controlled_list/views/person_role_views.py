from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import PersonRole
from controlled_list.serializers import PersonRoleSerializer, PersonRoleSelectSerializer


class PersonRoleList(generics.ListCreateAPIView):
    """
    Lists and creates person role entries.

    Person roles describe how an individual is related to a record
    (e.g., creator, interviewer, subject), enabling consistent indexing
    and display.
    """

    queryset = PersonRole.objects.all()
    serializer_class = PersonRoleSerializer


class PersonRoleDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single person role entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = PersonRole.objects.all()
    serializer_class = PersonRoleSerializer


class PersonRoleSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of person role entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: role
        - Returns results ordered by role
    """

    serializer_class = PersonRoleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('role',)
    queryset = PersonRole.objects.all().order_by('role')
