from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.authentication import BearerAuthentication
from workflow.file_name_parser import FileNameParser
from workflow.permission import APIGroupPermission
from workflow.serializers.container_serializers import ContainerDigitizedSerializer
from workflow.serializers.finding_aids_serializer import FindingAidsDigitizedSerializer


class DigitalObjectInfoView(APIView):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

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
