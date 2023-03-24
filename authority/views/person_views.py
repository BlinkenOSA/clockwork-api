from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Person
from authority.serializers import PersonSerializer, PersonSelectSerializer


class PersonList(generics.ListCreateAPIView):
    queryset = Person.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['last_name',]
    search_fields = ('first_name', 'last_name', 'personotherformat__first_name', 'personotherformat__last_name')
    serializer_class = PersonSerializer


class PersonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class PersonSelectList(generics.ListAPIView):
    serializer_class = PersonSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('last_name', 'first_name')
    queryset = Person.objects.all().order_by('last_name', 'first_name')
