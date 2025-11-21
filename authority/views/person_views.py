from django.db.models import Count, F
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Person
from authority.serializers import PersonSerializer, PersonSelectSerializer, PersonListSerializer


class PersonList(generics.ListCreateAPIView):
    queryset = Person.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['last_name', 'fa_subject_count', 'fa_associated_count', 'fa_total_count']
    search_fields = ('first_name', 'last_name', 'personotherformat__first_name', 'personotherformat__last_name')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PersonSerializer
        else:
            return PersonListSerializer

    def get_queryset(self):
        qs = Person.objects.annotate(
            fa_subject_count=Count('subject_poeple', distinct=True),
            fa_associated_count=Count(
                'findingaidsentityassociatedperson__fa_entity',
                distinct=True,
            ),
        ).annotate(
            fa_total_count=F('fa_subject_count') + F('fa_associated_count')
        )
        return qs

class PersonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class PersonSelectList(generics.ListAPIView):
    serializer_class = PersonSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('last_name', 'first_name', 'personotherformat__first_name', 'personotherformat__last_name')
    queryset = Person.objects.all().order_by('last_name', 'first_name')
