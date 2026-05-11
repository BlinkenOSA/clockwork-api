from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.authentication import BearerAuthentication
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity
from workflow.file_name_parser import FileNameParser
from workflow.permission import APIGroupPermission
from workflow.serializers.digital_object_request_response_serializers import (
    DigitalObjectUpsertResponseSerializer, DigitalObjectUpsertRequestSerializer,
)
from finding_aids.tasks import index_catalog_finding_aids_entity


class DigitalObjectUpsert(APIView):
    """
    Creates or updates a DigitalVersion record for a given filename, based on the URL.
    It can be either registering a master file, or an access copy uploaded to the catalog or to the Research Cloud.

    The endpoint:
    - validates filename pattern
    - resolves archival unit/container/finding aids entity
    - computes a normalized identifier and optional label
    - upserts a DigitalVersion record marked as available online
    - publishes the linked finding aids entity (if present)

    Authentication / Authorization:
    - BearerAuthentication or SessionAuthentication
    - Restricted to users in the ``Api`` group via APIGroupPermission
    """
    type = None

    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(
        operation_id='digital_version_upsert',
        operation_description="Creates or updates a DigitalVersion object based on the submitted file name.",
        request_body=DigitalObjectUpsertRequestSerializer(required=False),
        responses={
            200: DigitalObjectUpsertResponseSerializer(),
            400: 'Invalid filename'
        }
    )
    def post(self, request, file_name, *args, **kwargs):
        upsert_type = self.type
        technical_metadata = request.data.get('technical_metadata', None)

        file_name_parser = FileNameParser(file_name)

        if file_name_parser.matches_any_pattern():
            resolved_object = file_name_parser.resolve_archival_unit_or_container()

            lookup_fields = {
                'available_online': False,
                'available_research_cloud': False,
                'identifier': file_name_parser.get_doi(),
                'filename': file_name
            }

            updates = {
                'technical_metadata': technical_metadata
            }

            # If we are talking about master file
            if upsert_type == 'master':
                lookup_fields['level'] = 'M'
            # If we are talking about an access file upload to the research cloud
            elif upsert_type == 'access-rc':
                lookup_fields['level'] = 'A'
                lookup_fields['available_research_cloud'] = True
                updates['research_cloud_path'] = self._get_research_cloud_path(file_name, resolved_object['archival_unit'])
            # If we are talking about an access file upload to the catalog
            else:
                lookup_fields['level'] = 'A'
                lookup_fields['available_online'] = True
                lookup_fields['filename'] = self._transfer_av_filename(file_name)

            # If the resolved object is a Finding Aids Entity
            if resolved_object['finding_aids_entity']:
                lookup_fields['finding_aids_entity'] = resolved_object['finding_aids_entity']
            else:
                lookup_fields['container'] = resolved_object['container']

            dv, created = DigitalVersion.objects.update_or_create(
                **lookup_fields,
                defaults=updates
            )

            if dv.container:
                finding_aids_entities = FindingAidsEntity.objects.filter(
                    container=dv.container, is_template=False
                )
                for finding_aids_entity in finding_aids_entities.all():
                    index_catalog_finding_aids_entity.delay(finding_aids_entity.id)

            if dv.finding_aids_entity:
                index_catalog_finding_aids_entity.delay(dv.finding_aids_entity.id)

            return Response({
                'digital_version_id': dv.id,
                'action': 'created' if created else 'updated',
                'identifier': dv.identifier,
                'filename': dv.filename,
            }, status=200)

        else:
            return Response({'error': 'Invalid filename'}, status=400)

    @staticmethod
    def _transfer_av_filename(file_name):
        doi, _, extension = file_name.rpartition(".")
        if extension == '.mp4':
            return file_name.replace('.mp4', '.m3u8')
        return file_name

    @staticmethod
    def _get_research_cloud_path(file_name, archival_unit):
        fonds = archival_unit.get_fonds().reference_code
        subfonds = archival_unit.get_subfonds().reference_code
        series = archival_unit.reference_code

        return f'{fonds}/{subfonds}/{series}/{file_name}'