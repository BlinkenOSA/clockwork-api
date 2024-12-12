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
    permission_classes = []

    def post(self, request):
        serializer = ResearchRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            researcher = Researcher.objects.get(id=data['researcher'])

            request, created = Request.objects.get_or_create(
                researcher=researcher,
                request_date=data['request_date']
            )

            items = data.get('items', [])
            for item in items:
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
                    if finding_aids_entity.restricted:
                        request_item_restriction, created = RequestItemRestriction.objects.get_or_create(
                            request_item=request_item
                        )
                        if created:
                            # Send out email about the restricted form stuff
                            pass

                else:
                    request_item, created = RequestItem.objects.get_or_create(
                        request=request,
                        item_origin=item['origin'],
                        title=item['title'],
                        identifier=item['call_number'],
                        library_id=item['library_id'],
                        quantity=item['volume'] if 'volume' in item.keys() else ''
                    )

            # Email template
            mail = EmailWithTemplate(
                researcher=researcher,
                context={
                    'researcher': researcher,
                    'request': request,
                    'items': items
                }
            )

            # Send out admin email.
            mail.send_new_request_admin()
            mail.send_new_request_user()
            return Response('ok', status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=404)
