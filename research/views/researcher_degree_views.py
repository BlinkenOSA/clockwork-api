from rest_framework import generics
from rest_framework.filters import SearchFilter

from research.models import ResearcherDegree
from research.serializers.researcher_degree_serializers import ResearcherDegreeReadSerializer, \
    ResearcherDegreeWriteSerializer, ResearcherDegreeSerializer


class ResearcherDegreeList(generics.ListCreateAPIView):
    queryset = ResearcherDegree.objects.all().order_by('degree')
    filter_backends = SearchFilter
    search_fields = ('degree',)
    method_serializer_classes = {
        ('GET', ): ResearcherDegreeReadSerializer,
        ('POST', ): ResearcherDegreeWriteSerializer
    }


class ResearcherDegreeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ResearcherDegree.objects.all()
    method_serializer_classes = {
        ('GET', ): ResearcherDegreeReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ResearcherDegreeWriteSerializer
    }


class ResearcherDegreeSelectList(generics.ListAPIView):
    serializer_class = ResearcherDegreeSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['degree']
    queryset = ResearcherDegree.objects.all().order_by('degree')
