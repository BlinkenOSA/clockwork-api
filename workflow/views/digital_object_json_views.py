from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.authentication import BearerAuthentication
from workflow.file_name_parser import FileNameParser
from workflow.permission import APIGroupPermission

from workflow.serializers.digital_version_json_serializers import DigitalObjectJSONSerializer


class DigitalObjectJSONView(APIView):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(
        operation_id='digital_object_json_export',
        operation_description="Exports archival metadata resolved from the submitted file name as JSON",
        responses={
            400: 'Invalid filename'
        }
    )
    def get(self, request, file_name, *args, **kwargs):
        file_name_parser = FileNameParser(file_name)

        if not file_name_parser.matches_any_pattern():
            return Response({'error': 'Invalid filename'}, status=400)

        resolved_object = file_name_parser.resolve_archival_unit_or_container()

        if resolved_object['container'] is not None or resolved_object['finding_aids_entity'] is not None:
            serializer = DigitalObjectJSONSerializer(resolved_object)
            return Response(serializer.data)

        return Response({'error': 'Could not resolve archival object'}, status=400)
