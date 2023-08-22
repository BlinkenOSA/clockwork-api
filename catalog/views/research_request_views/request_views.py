from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from catalog.serializers.research_request_serializer import ResearchRequestSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from container.models import Container
from research.models import Request, Researcher, RequestItem


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
                else:
                    request_item, created = RequestItem.objects.get_or_create(
                        request=request,
                        item_origin=item['origin'],
                        title=item['title'],
                        identifier=item['call_number']
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
