from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter

from authority.models import Country
from authority.serializers import CountrySelectSerializer
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from controlled_list.models import Nationality
from controlled_list.serializers import NationalitySelectSerializer
from research.models import Researcher
from research.serializers.researcher_serializers import ResearcherReadSerializer, ResearcherWriteSerializer, \
    ResearcherSelectSerializer


class ResearcherList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Researcher.objects.all().order_by('-date_created')
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['last_name', ]
    search_fields = ('first_name', 'last_name',)
    method_serializer_classes = {
        ('GET', ): ResearcherReadSerializer,
        ('POST', ): ResearcherWriteSerializer
    }


class ResearcherDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Researcher.objects.all()
    method_serializer_classes = {
        ('GET', ): ResearcherReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ResearcherWriteSerializer
    }


class ResearcherSelectList(generics.ListAPIView):
    serializer_class = ResearcherSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['first_name', 'last_name']
    queryset = Researcher.objects.all().order_by('last_name', 'first_name')


class ResearcherCountrySelectList(generics.ListAPIView):
    serializer_class = CountrySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['country', 'alpha2', 'alpha3']
    queryset = Country.objects.all().order_by('country')


class ResearcherNationalitySelectList(generics.ListAPIView):
    serializer_class = NationalitySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['nationality']
    queryset = Nationality.objects.all().order_by('nationality')
