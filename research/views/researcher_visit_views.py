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
    queryset = ResearcherVisit.objects.all().order_by('-check_in')
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ['researcher']
    search_fields = ['researcher__last_name', 'researcher__first_name', 'researcher__email', 'researcher__card_number']
    ordering_fields = ['researcher__last_name', 'researcher__first_name', 'researcher__card_number', 'researcher__email', 'check_in', 'check_out']
    serializer_class = ResearcherVisitListSerializer


class ResearcherVisitsCheckIn(APIView):
    def post(self, request, *args, **kwargs):
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
    def put(self, request, *args, **kwargs):
        visit_id = self.kwargs.get('pk')
        visit = get_object_or_404(ResearcherVisit, pk=visit_id)

        # If check out is on the same day, then current date:
        if visit.check_in.day == datetime.datetime.now().day:
            visit.check_out = datetime.datetime.now()
        # else check out should happen on the same day at 18:00
        else:
            ci = visit.check_in
            visit.check_out = datetime.datetime(ci.year, ci.month, ci.day, 18, 00, 00)

        visit.save()
        return Response(status=status.HTTP_200_OK)
