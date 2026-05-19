from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.authentication import BearerAuthentication
from workflow.file_name_parser import FileNameParser
from workflow.permission import APIGroupPermission
from workflow.services.ead_exporter import EADExporter


class DigitalObjectEADView(APIView):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(
        operation_id='digital_object_ead_export',
        operation_description="Exports archival metadata resolved from the submitted file name as EAD XML.",
        responses={
            200: openapi.Response(
                description="A valid EAD XML document will be returned as the response body."
            ),
            400: 'Invalid filename'
        }
    )
    def get(self, request, file_name, *args, **kwargs):
        file_name_parser = FileNameParser(file_name)

        if not file_name_parser.matches_any_pattern():
            return Response({'error': 'Invalid filename'}, status=400)

        resolved_object = file_name_parser.resolve_archival_unit_or_container()
        exporter = EADExporter()

        if resolved_object['level'] == 'container' and resolved_object['container'] is not None:
            xml = exporter.render_for_container(resolved_object['container'], file_name)
            return HttpResponse(xml, content_type='application/xml; charset=utf-8')

        if resolved_object['finding_aids_entity'] is not None:
            xml = exporter.render_for_finding_aids_entity(resolved_object['finding_aids_entity'], file_name)
            return HttpResponse(xml, content_type='application/xml; charset=utf-8')

        return Response({'error': 'Could not resolve archival object'}, status=400)
