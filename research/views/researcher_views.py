from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from authority.models import Country
from authority.serializers import CountrySelectSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from controlled_list.models import Nationality
from controlled_list.serializers import NationalitySelectSerializer
from research.models import Researcher
from django_filters import rest_framework as filters
from research.serializers.researcher_serializers import ResearcherReadSerializer, ResearcherWriteSerializer, \
    ResearcherSelectSerializer, ResearcherListSerializer


class ResearcherFilterClass(filters.FilterSet):
    """
    FilterSet for researchers.

    Provides a free-text ``search`` filter that matches researcher names across:
        - first name
        - last name
        - middle name
    """

    search = filters.CharFilter(label='Search', method='filter_search')

    def filter_search(self, queryset, name, value):
        """
        Applies a case-insensitive search over researcher name fields.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Search string.

        Returns:
            A queryset filtered by name matches.
        """
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(middle_name__icontains=value)
        )


class ResearcherList(MethodSerializerMixin, generics.ListCreateAPIView):
    """
    Lists researchers or creates a new researcher.

    GET:
        Returns researchers using ResearcherListSerializer.

    POST:
        Creates a researcher using ResearcherWriteSerializer.

    Features:
        - Filtering by country, citizenship, active, approved
        - Name search via ResearcherFilterClass
        - Ordering by identity and administrative fields
        - Dynamic serializer selection based on HTTP method
    """

    queryset = Researcher.objects.all().order_by('-date_created', 'last_name', 'first_name')
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['country', 'citizenship', 'active', 'approved']
    filterset_class = ResearcherFilterClass
    ordering_fields = [
        'last_name',
        'first_name',
        'card_number',
        'country__country',
        'citizenship__nationality',
        'date_created'
    ]
    method_serializer_classes = {
        ('GET', ): ResearcherListSerializer,
        ('POST', ): ResearcherWriteSerializer
    }


class ResearcherDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single researcher.

    GET:
        Uses ResearcherReadSerializer.

    PUT/PATCH/DELETE:
        Uses ResearcherWriteSerializer.
    """

    queryset = Researcher.objects.all()
    method_serializer_classes = {
        ('GET', ): ResearcherReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ResearcherWriteSerializer
    }


class ResearcherSelectList(generics.ListAPIView):
    """
    Lightweight list of approved and active researchers for selection UIs.

    Features:
        - Unpaginated output
        - Name search via ResearcherFilterClass
        - Restricted to researchers with active=True and approved=True
    """

    serializer_class = ResearcherSelectSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ResearcherFilterClass
    queryset = Researcher.objects.filter(active=True, approved=True).order_by('last_name', 'first_name')


class ResearcherCountrySelectList(generics.ListAPIView):
    """
    Selection endpoint returning all countries.

    Intended for dropdowns/autocomplete components used during researcher
    registration and editing.
    """

    serializer_class = CountrySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['country', 'alpha2', 'alpha3']
    queryset = Country.objects.all().order_by('country')


class ResearcherCountryActiveSelectList(generics.ListAPIView):
    """
    Selection endpoint returning only countries used by at least one researcher.

    This is useful for filter dropdowns where only "in use" values should be shown.
    """

    serializer_class = CountrySelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['country', 'alpha2', 'alpha3']

    def get_queryset(self):
        """
        Returns countries that appear in researcher records.

        Returns:
            A queryset of distinct countries referenced by researchers.
        """
        countries = Researcher.objects.values_list('country__id', flat=True).distinct()
        return Country.objects.filter(id__in=countries)


class ResearcherNationalitySelectList(generics.ListAPIView):
    """
    Selection endpoint returning all nationalities.

    Intended for dropdowns/autocomplete components used during researcher
    registration and editing.
    """

    serializer_class = NationalitySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['nationality']
    queryset = Nationality.objects.all().order_by('nationality')


class ResearcherNationalityActiveSelectList(generics.ListAPIView):
    """
    Selection endpoint returning only nationalities used by at least one researcher.

    This is useful for filter dropdowns where only "in use" values should be shown.
    """

    serializer_class = NationalitySelectSerializer
    pagination_class = None
    permission_classes = []
    filter_backends = (SearchFilter,)
    search_fields = ['nationality']

    def get_queryset(self):
        """
        Returns nationalities that appear in researcher records.

        Returns:
            A queryset of distinct nationalities referenced by researchers.
        """
        nationalities = Researcher.objects.values_list('citizenship__id', flat=True).distinct()
        return Nationality.objects.filter(id__in=nationalities)


class ResearcherActivate(APIView):
    """
    Activates or deactivates a researcher.

    PUT /researcher/<action>/<pk>/ where action is:
        - activate
        - deactivate

    The action toggles the researcher's ``active`` flag.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the activation state change.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing ``action`` and ``pk``.

        Returns:
            200 OK after updating the researcher.
        """
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
    """
    Approves or disapproves a researcher.

    PUT /researcher/<action>/<pk>/ where action is:
        - approve
        - disapprove

    Side effects:
        - On approval, sends an "account approved" email to the researcher.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the approval state change.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing ``action`` and ``pk``.

        Returns:
            200 OK after updating the researcher.
        """
        action = self.kwargs.get('action')
        researcher_id = self.kwargs.get('pk')
        researcher = get_object_or_404(Researcher, pk=researcher_id)

        if action == 'approve':
            researcher.approved = True
            researcher.save()

            mail = EmailWithTemplate(
                researcher=researcher,
                context={'researcher': researcher}
            )
            mail.send_new_user_approved_user()

            return Response(status=status.HTTP_200_OK)
        else:
            researcher.approved = False
            researcher.save()
            return Response(status=status.HTTP_200_OK)
