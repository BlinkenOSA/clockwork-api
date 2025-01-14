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
    researcher = filters.CharFilter(label='Researcher', method='filter_researcher')
    status = filters.CharFilter(label='Status', method='filter_status')
    request_date = filters.CharFilter(label='Request Date', method='filter_request_date')

    def filter_researcher(self, queryset, name, value):
        return queryset.filter(request_item__request__researcher=value)

    def filter_status(self, queryset, name, value):
        return queryset.filter(status=value)


class RestrictedRequestsList(generics.ListAPIView):
    queryset = (RequestItemPart.objects.filter(
        finding_aids_entity__access_rights__statement='Restricted',
        request_item__request__request_date__gte='2025-01-01'
    )
                .order_by('-request_item__request__created_date'))
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = RestrictedRequestFilterClass
    search_fields = ['request_item__request__researcher__last_name', 'request_item__request__researcher__first_name',
                     'request_item__container__archival_unit__reference_code',
                     'request_item__container__barcode']
    ordering_fields = ['request_item__request__researcher__last_name', 'status', 'request_item__request__request_date']
    serializer_class = RestrictedRequestsListSerializer


class RestrictedRequestAction(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action', None)
        request_item_part_id = self.kwargs.get('request_item_part_id', None)
        decision = None

        try:
            request_item_part = RequestItemPart.objects.get(id=request_item_part_id)

            if action == 'approve':
                request_item_part.status = 'approved'
                decision = 'Access granted (with conditions)'
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
                        'decision': decision
                    }
                )

                mail.send_new_request_restricted_decision_user()

            return Response(status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
