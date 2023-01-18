from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter

from research.models import ResearcherVisit
from research.serializers.researcher_visit_serializers import ResearcherVisitListSerializer


class ResearcherVisitsList(ListAPIView):
    queryset = ResearcherVisit.objects.all().order_by('-check_in')
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ['researcher']
    ordering_fields = ['last_name', 'first_name', 'check_in', 'check_out']
    serializer_class = ResearcherVisitListSerializer
