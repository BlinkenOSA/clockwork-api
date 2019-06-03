from rest_framework import generics
from rest_framework.filters import SearchFilter

from authority.models import Subject
from authority.serializers import SubjectSerializer, SubjectSelectSerializer


class SubjectList(generics.ListCreateAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class SubjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class SubjectSelectList(generics.ListAPIView):
    serializer_class = SubjectSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('subject',)
    queryset = Subject.objects.all().order_by('subject')
