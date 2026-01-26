import datetime

from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.mailer.email_with_template import EmailWithTemplate
from controlled_list.models import AccessRight
from research.models import RequestItem, Request, RequestItemPart
from django_filters import rest_framework as filters

from research.serializers.restricted_requests_serializers import RestrictedRequestsListSerializer


class RestrictedRequestFilterClass(filters.FilterSet):
    """
    FilterSet for restricted request item parts.

    Supports filtering by:
        - researcher (parent request's researcher)
        - part workflow status (new/approved/approved_on_site/rejected/lifted)
        - request date bucket (declared but not implemented in this snippet)

    Notes:
        - ``request_date`` is declared on the FilterSet but there is no
          ``filter_request_date`` method defined here. If date filtering is
          required, implement the method or remove the filter field.
    """

    researcher = filters.CharFilter(label='Researcher', method='filter_researcher')
    status = filters.CharFilter(label='Status', method='filter_status')
    request_date = filters.CharFilter(label='Request Date', method='filter_request_date')

    def filter_researcher(self, queryset, name, value):
        """
        Filters restricted parts by researcher identifier.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Researcher identifier (typically PK).

        Returns:
            A queryset filtered to parts belonging to the given researcher.
        """
        return queryset.filter(request_item__request__researcher=value)

    def filter_status(self, queryset, name, value):
        """
        Filters restricted parts by workflow status.

        Args:
            queryset: Base queryset provided by the view.
            name: Field name (required by the django-filter API).
            value: Status string (e.g. 'new', 'approved', 'rejected').

        Returns:
            A queryset filtered by the given status.
        """
        return queryset.filter(status=value)


class RestrictedRequestsList(generics.ListAPIView):
    """
    Lists restricted request item parts for review and decision workflows.

    The queryset is restricted to:
        - parts whose linked finding aids entity is currently marked "Restricted"
        - requests with request_date >= 2025-01-01

    Features:
        - Filtering via RestrictedRequestFilterClass
        - Search by researcher name and container identifiers
        - Ordering by researcher last name, status, and request date
    """

    queryset = (
        RequestItemPart.objects.filter(
            finding_aids_entity__access_rights__statement='Restricted',
            request_item__request__request_date__gte='2025-01-01'
        )
        .order_by('-request_item__request__created_date')
    )
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = RestrictedRequestFilterClass
    search_fields = [
        'request_item__request__researcher__last_name',
        'request_item__request__researcher__first_name',
        'request_item__container__archival_unit__reference_code',
        'request_item__container__barcode',
    ]
    ordering_fields = [
        'request_item__request__researcher__last_name',
        'status',
        'request_item__request__request_date',
    ]
    serializer_class = RestrictedRequestsListSerializer


class RestrictedRequestAction(APIView):
    """
    Performs a decision action on a restricted request item part.

    PUT /restricted-requests/<action>/<request_item_part_id>/

    Supported actions:
        - approve: sets status='approved' and records a conditional approval decision
        - approve_on_site: sets status='approved_on_site' and records on-site-only approval
        - reject: sets status='rejected'
        - lift: sets status='lifted' and also updates the linked finding aids entity to "Not restricted"
        - undo: resets status='new'

    Side effects:
        - Records decision timestamp and decision maker username.
        - Sends decision notification emails to the researcher and admins for actions
          other than ``undo``.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the requested decision action to the target RequestItemPart.

        Args:
            request: DRF request.
            *args: Positional args passed by DRF.
            **kwargs: Keyword args containing ``action`` and ``request_item_part_id``.

        Returns:
            200 OK on success,
            400 BAD REQUEST for an unsupported action,
            404 NOT FOUND if the part does not exist.
        """
        action = self.kwargs.get('action', None)
        request_item_part_id = self.kwargs.get('request_item_part_id', None)
        decision = None

        try:
            request_item_part = RequestItemPart.objects.get(id=request_item_part_id)

            if action == 'approve':
                request_item_part.status = 'approved'
                decision = 'Access granted (with conditions)'
            elif action == 'approve_on_site':
                request_item_part.status = 'approved_on_site'
                decision = 'Access granted (on-site viewing only)'
            elif action == 'reject':
                request_item_part.status = 'rejected'
                decision = 'Access denied'
            elif action == 'lift':
                request_item_part.status = 'lifted'
                decision = 'Access granted'

                access_right = AccessRight.objects.get(statement='Not restricted')
                request_item_part.finding_aids_entity.access_rights = access_right
                request_item_part.finding_aids_entity.save()

            elif action == 'undo':
                request_item_part.status = 'new'
            else:
                return Response("wrong action type", status=status.HTTP_400_BAD_REQUEST)

            request_item_part.decision_date = datetime.datetime.now()
            request_item_part.decision_by = request.user.username
            request_item_part.save()

            if action != 'undo':
                mail = EmailWithTemplate(
                    researcher=request_item_part.request_item.request.researcher,
                    context={
                        'researcher': request_item_part.request_item.request.researcher,
                        'archival_reference_code': request_item_part.finding_aids_entity.archival_reference_code,
                        'title': request_item_part.finding_aids_entity.title,
                        'decision': decision,
                        'decision_maker': request.user.username
                    }
                )

                mail.send_new_request_restricted_decision_user()
                mail.send_new_request_restricted_decision_admin()

            return Response(status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
