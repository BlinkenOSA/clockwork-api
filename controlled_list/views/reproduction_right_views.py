from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import ReproductionRight
from controlled_list.serializers import ReproductionRightSerializer, ReproductionRightSelectSerializer


class ReproductionRightList(generics.ListCreateAPIView):
    """
    Lists and creates reproduction right entries.

    Reproduction rights standardize statements governing how materials
    may be reproduced, copied, or reused.
    """

    queryset = ReproductionRight.objects.all()
    serializer_class = ReproductionRightSerializer


class ReproductionRightDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single reproduction right entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = ReproductionRight.objects.all()
    serializer_class = ReproductionRightSerializer


class ReproductionRightSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of reproduction right entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: statement
        - Returns results ordered by statement
    """

    serializer_class = ReproductionRightSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('statement',)
    queryset = ReproductionRight.objects.all().order_by('statement')
