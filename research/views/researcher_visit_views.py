import datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from research.models import ResearcherVisit, Researcher
from research.serializers.researcher_visit_serializers import ResearcherVisitListSerializer


class ResearcherVisitsList(ListAPIView):
    """
    Lists researcher visit records.

    Returns :class:`research.models.ResearcherVisit` entries ordered by most
    recent check-in first.

    Features:
        - Filtering by researcher
        - Search across researcher identity fields
        - Ordering by researcher fields and visit timestamps
    """

    queryset = ResearcherVisit.objects.all().order_by('-check_in')
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ['researcher']
    search_fields = ['researcher__last_name', 'researcher__first_name', 'researcher__email', 'researcher__card_number']
    ordering_fields = [
        'researcher__last_name',
        'researcher__first_name',
        'researcher__card_number',
        'researcher__email',
        'check_in',
        'check_out'
    ]
    serializer_class = ResearcherVisitListSerializer


class ResearcherVisitsCheckIn(APIView):
    """
    Creates a new visit (check-in) for a researcher.

    POST /visits/check-in/<researcher_id>

    Rules:
        - A researcher may have only one open visit at a time (check_out is null).
        - If an open visit exists, returns 400 with an explanatory message.
    """

    def post(self, request, *args, **kwargs):
        """
        Checks the researcher in by creating a new visit if none is open.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing ``researcher_id``.

        Returns:
            200 OK when the visit is created, or 400 if an open visit already exists.
        """
        researcher_id = self.kwargs.get('researcher_id')
        researcher = get_object_or_404(Researcher, pk=researcher_id)

        open_visits = ResearcherVisit.objects.filter(researcher=researcher, check_out__isnull=True)

        if open_visits.count() == 0:
            ResearcherVisit.objects.create(researcher=researcher)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The researcher already has an open visit.\nPlease close that one first!"
            )


class ResearcherVisitsCheckOut(APIView):
    """
    Closes an open visit (check-out) for a researcher visit record.

    PUT /visits/check-out/<pk>

    Behavior:
        - If check-out happens on the same day as check-in, sets check_out to now.
        - Otherwise, sets check_out to the check-in day at 17:45.
    """

    def put(self, request, *args, **kwargs):
        """
        Checks a visit out by setting ``check_out`` and saving.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing visit PK as ``pk``.

        Returns:
            200 OK after updating the visit.
        """
        visit_id = self.kwargs.get('pk')
        visit = get_object_or_404(ResearcherVisit, pk=visit_id)

        # If check out is on the same day, then current date:
        if visit.check_in.day == datetime.datetime.now().day:
            visit.check_out = datetime.datetime.now()
        # else check out should happen on the same day at 18:00
        else:
            ci = visit.check_in
            visit.check_out = datetime.datetime(ci.year, ci.month, ci.day, 17, 45, 00)

        visit.save()
        return Response(status=status.HTTP_200_OK)
