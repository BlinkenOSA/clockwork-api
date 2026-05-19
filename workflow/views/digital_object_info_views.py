from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.authentication import BearerAuthentication
from workflow.file_name_parser import FileNameParser
from workflow.permission import APIGroupPermission
from workflow.serializers.container_serializers import ContainerDigitizedSerializer
from workflow.serializers.digital_object_request_response_serializers import DigitalVersionInfoSerializer
from workflow.serializers.finding_aids_serializer import FindingAidsDigitizedSerializer


class DigitalObjectInfoView(APIView):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(
        operation_id='digital_version_info',
        operation_description="Returns information about the object based on the submitted file name.",
        responses={
            200: DigitalVersionInfoSerializer(),
            400: 'Invalid filename'
        }
    )
    def get(self, request, file_name, *args, **kwargs):
        file_name_parser = FileNameParser(file_name)

        if not file_name_parser.matches_any_pattern():
            return Response({'error': 'Invalid filename'}, status=400)

        resolved_object = file_name_parser.resolve_archival_unit_or_container()

        if resolved_object['level'] == 'container' and resolved_object['container'] is not None:
            serializer = ContainerDigitizedSerializer(resolved_object['container'])
            return Response(serializer.data)

        if resolved_object['finding_aids_entity'] is not None:
            serializer = FindingAidsDigitizedSerializer(resolved_object['finding_aids_entity'])
            return Response(serializer.data)

        return Response({'error': 'Could not resolve archival object'}, status=400)
