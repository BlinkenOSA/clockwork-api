from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from authority.models import Country
from authority.serializers import CountrySelectSerializer
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from clockwork_api.pagination import DropDownResultSetPagination
from controlled_list.models import Nationality
from controlled_list.serializers import NationalitySelectSerializer
from research.models import Researcher
from django_filters import rest_framework as filters
from research.serializers.researcher_serializers import ResearcherReadSerializer, ResearcherWriteSerializer, \
    ResearcherSelectSerializer, ResearcherListSerializer


class ResearcherFilterClass(filters.FilterSet):
    search = filters.CharFilter(label='Search', method='filter_search')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(middle_name__icontains=value)
        )


class ResearcherList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Researcher.objects.all().order_by('-date_created', 'last_name', 'first_name')
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ['country', 'citizenship', 'active', 'approved']
    filterset_class = ResearcherFilterClass
    ordering_fields = ['last_name', 'first_name', 'card_number', 'country__country', 'citizenship__nationality', 'date_created']
    method_serializer_classes = {
        ('GET', ): ResearcherListSerializer,
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
    queryset = Researcher.objects.filter(active=True, approved=True).order_by('last_name', 'first_name')


class ResearcherCountrySelectList(generics.ListAPIView):
    serializer_class = CountrySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['country', 'alpha2', 'alpha3']
    queryset = Country.objects.all().order_by('country')


class ResearcherCountryActiveSelectList(generics.ListAPIView):
    serializer_class = CountrySelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['country', 'alpha2', 'alpha3']

    def get_queryset(self):
        countries = Researcher.objects.values_list('country__id', flat=True).distinct()
        return Country.objects.filter(id__in=countries)


class ResearcherNationalitySelectList(generics.ListAPIView):
    serializer_class = NationalitySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['nationality']
    queryset = Nationality.objects.all().order_by('nationality')


class ResearcherNationalityActiveSelectList(generics.ListAPIView):
    serializer_class = NationalitySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['nationality']

    def get_queryset(self):
        nationalities = Researcher.objects.values_list('citizenship__id', flat=True).distinct()
        return Nationality.objects.filter(id__in=nationalities)


class ResearcherActivate(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        researcher_id = self.kwargs.get('pk')
        researcher = get_object_or_404(Researcher, pk=researcher_id)

        if action == 'activate':
            researcher.active = True
            researcher.save()
            return Response(status=status.HTTP_200_OK)
        else:
            researcher.active = False
            researcher.save()
            return Response(status=status.HTTP_200_OK)


class ResearcherApprove(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        researcher_id = self.kwargs.get('pk')
        researcher = get_object_or_404(Researcher, pk=researcher_id)

        if action == 'approve':
            researcher.approved = True
            researcher.save()
            return Response(status=status.HTTP_200_OK)
        else:
            researcher.approved = False
            researcher.save()
            return Response(status=status.HTTP_200_OK)