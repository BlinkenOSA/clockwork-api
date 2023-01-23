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
    ordering_fields = ['last_name', 'first_name', 'check_in', 'check_out']
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
        visit.check_out = datetime.datetime.now()
        visit.save()
        return Response(status=status.HTTP_200_OK)
