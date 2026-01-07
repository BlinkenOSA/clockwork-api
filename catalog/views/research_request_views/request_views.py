"""
Public endpoint for submitting archival research requests.

This module implements the main workflow for researchers to request
archival materials (finding aids or external/library items).

The endpoint:
    - validates researcher identity via email + card number
    - validates request items
    - creates or reuses a Request record
    - creates request items and item parts
    - detects restricted content
    - sends notification emails to relevant parties

This endpoint is intentionally unauthenticated and protected via:
    - hCaptcha
    - strict validation rules
    - external rate limiting
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from catalog.serializers.research_request_serializer import ResearchRequestSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from container.models import Container
from finding_aids.models import FindingAidsEntity
from research.models import Request, Researcher, RequestItem, RequestItemPart, RequestItemRestriction


class ResearcherRequestView(APIView):
    """
    Handles submission of archival research requests.

    This endpoint processes a complete research request, including:
        - researcher identification
        - requested items
        - restriction handling
        - email notifications

    The endpoint is designed to be idempotent per researcher and request_date.
    """

    permission_classes = []

    def post(self, request) -> Response:
        """
        Submits a new research request.

        Expected request payload:
            - researcher identity (email + card_number)
            - request_date
            - one or more request items
            - hCaptcha token
            - optional research subject and motivation

        Validation:
            - researcher identity must match an existing Researcher
            - request items must be valid and resolvable
            - hCaptcha must be verified

        Side effects:
            - Creates or reuses a Request record
            - Creates RequestItem, RequestItemPart, and restriction records
            - Sends email notifications to:
                * researcher
                * administrators
                * restriction decision makers (if applicable)

        Returns:
            HTTP 200 with "ok" on success.
        """
        serializer = ResearchRequestSerializer(data=request.data)

        has_restricted_content = False

        # Serializer validation
        if serializer.is_valid():
            data = serializer.data

            # Researcher resolution
            # Researcher identity is resolved in the serializer and trusted here.
            researcher = Researcher.objects.get(id=data['researcher'])

            # Request creation
            # A researcher can only have one request per date.
            request, created = Request.objects.get_or_create(
                researcher=researcher,
                request_date=data['request_date']
            )

            # Item processing loop
            items = data.get('items', [])
            for item in items:
                # Finding Aids Item
                if item['origin'] == 'FA':
                    request_item, created = RequestItem.objects.get_or_create(
                        request=request,
                        item_origin=item['origin'],
                        container=Container.objects.get(id=item['container']),
                    )

                    try:
                        finding_aids_entity = FindingAidsEntity.objects.get(id=item['ams_id'])
                    except ObjectDoesNotExist:
                        break

                    request_item_part, created = RequestItemPart.objects.get_or_create(
                        request_item=request_item,
                        finding_aids_entity=finding_aids_entity
                    )

                    # Handle restriction
                    if finding_aids_entity.restricted:
                        has_restricted_content = True
                        request_item_restriction, created = RequestItemRestriction.objects.get_or_create(
                            request_item=request_item
                        )
                        # Set the restriction data
                        request_item_restriction.research_subject = data['research_subject']
                        request_item_restriction.motivation = data['motivation']
                        request_item_restriction.save()

                # Library/Film Library Item
                else:
                    request_item, created = RequestItem.objects.get_or_create(
                        request=request,
                        item_origin=item['origin'],
                        title=item['title'],
                        identifier=item['call_number'],
                        library_id=item['ams_id'],
                        quantity=item['volume'] if 'volume' in item.keys() else ''
                    )

            # Notification email template
            mail = EmailWithTemplate(
                researcher=researcher,
                context={
                    'researcher': researcher,
                    'request': request,
                    'items': items,
                    'has_restricted_content': has_restricted_content,
                    'research_subject': data['research_subject'] if 'research_subject' in data else '',
                    'motivation': data['motivation'] if 'motivation' in data else ''
                }
            )

            # Send out admin email.
            mail.send_new_request_admin()
            mail.send_new_request_user()

            # Send out restricted content email to decision makers
            if has_restricted_content:
                mail.send_new_request_restricted_decision_maker()

            return Response('ok', status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=404)
