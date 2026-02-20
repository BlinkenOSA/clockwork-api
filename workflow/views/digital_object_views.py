import mimetypes
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from clockwork_api.authentication import BearerAuthentication
from container.models import Container
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity
from workflow.permission import APIGroupPermission
from workflow.serializers.digital_object_serializers import (
    DigitalObjectInfoResponseSerializer,
    DigitalObjectUpsertResponseSerializer,
)


def matches_any_pattern(s):
    """
    Validates whether a submitted filename matches any supported DOI patterns.

    The workflow endpoints accept access copy filenames that encode a DOI-like
    identifier in the filename prefix. This helper validates the full filename,
    including extension.

    Supported examples:
        - HU_OSA_386_1_1_0001.pdf
        - HU_OSA_386_1_1_0001_0001.jpg
        - HU_OSA_386_1_1_0001_0001_P001.tif
        - HU_OSA_386_1_1_0001_0001_0001_P001.mp4
        - HU_OSA_11112222.mkv

    Args:
        s: Filename string (including extension).

    Returns:
        bool: True if the filename matches a supported pattern.
    """
    patterns = [
        # HU_OSA_386_1_1_0001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}\.[a-zA-Z0-9]+$',

        # HU_OSA_386_1_1_0001_0001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}\.[a-zA-Z0-9]+$',

        # HU_OSA_386_1_1_0001_0001_P001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_P\d{3}\.[a-zA-Z0-9]+$',

        # HU_OSA_384_0_2_0023_0001_P050_A (special cases for the Bartok Collection)
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_P\d{3}_[a-zA-Z]\.[a-zA-Z0-9]+$',

        # HU_OSA_386_1_1_0001_0001_0001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_\d{4}\.[a-zA-Z0-9]+$',

        # HU_OSA_386_1_1_0001_0001_0001_P001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_\d{4}_P\d{3}\.[a-zA-Z0-9]+$',

        # HU_OSA_11112222
        r'HU_OSA_\d{8}\.[a-zA-Z0-9]+$'
    ]
    return any(re.fullmatch(p, s) for p in patterns)


def get_access_copy_actions(doi, primary_type):
    """
    Computes destination paths for an access copy and its thumbnail.

    The returned payload tells workflow clients where to upload:
        - the access copy (file)
        - an optional thumbnail

    Resolution depends on the primary_type and uses settings-defined
    storage servers and base directories.

    Args:
        doi: Digital object identifier (without extension).
        primary_type: One of "Textual", "Still Image", "Moving Image", "Audio".

    Returns:
        dict: Mapping with target_server, target_path, thumbnail_path, and filename.
    """
    doi_parts = doi.split("_")

    data = {
        'target_server': '',
        'target_path': '',
        'thumbnail_path': '',
    }

    if primary_type == 'Textual':
        data['target_server'] = getattr(settings, 'DIGITAL_OBJECTS_STORAGE_TEXT_SERVER', '')
        main_dir = '_'.join(doi_parts[:5])
        sub_dir = '_'.join(doi_parts[:6])
        if len(doi_parts) == 7:
            filename = '_'.join(doi_parts[:7])
        else:
            filename = '_'.join(doi_parts[:8])
        data['filename'] = f'{filename}.pdf'
        data['target_path'] = (
            f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_TEXT_BASE_DIR", "")}'
            f'{main_dir}/{sub_dir}/{filename}.pdf'
        )
        data['thumbnail_path'] = (
            f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_TEXT_BASE_DIR", "")}'
            f'{main_dir}/{sub_dir}/{filename}.jpg'
        )

    elif primary_type == 'Still Image':
        data['target_server'] = getattr(settings, 'DIGITAL_OBJECTS_STORAGE_IMAGE_SERVER', '')
        # NOTE: Existing code sets target_path twice and then clears it. Preserved behavior.
        data['target_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_IMAGE_BASE_DIR", "")}'
        data['target_path'] = ''
        data['filename'] = f'{doi}.jpg'

    elif primary_type == 'Moving Image':
        main_dir = '_'.join(doi_parts[:5])
        if len(doi_parts) == 6:
            new_parts = doi_parts[:5] + ['0001']
            sub_dir = '_'.join(new_parts)
        else:
            sub_dir = '_'.join(doi_parts[:6])

        data['target_server'] = getattr(settings, 'DIGITAL_OBJECTS_STORAGE_VIDEO_SERVER', '')
        data['filename'] = f'{sub_dir}_0001.m3u8'
        data['target_path'] = (
            f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_VIDEO_BASE_DIR", "")}'
            f'{main_dir}/{sub_dir}/{sub_dir}_0001.m3u8'
        )
        data['thumbnail_path'] = (
            f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_VIDEO_BASE_DIR", "")}'
            f'{main_dir}/{sub_dir}/{sub_dir}_0001.jpg'
        )

    elif primary_type == 'Audio':
        data['target_server'] = getattr(settings, 'DIGITAL_OBJECTS_STORAGE_AUDIO_SERVER', '')
        main_dir = '_'.join(doi_parts[:5])
        if len(doi_parts) == 6:
            new_parts = doi_parts[:5] + ['0001']
            file = '_'.join(new_parts)
        else:
            file = '_'.join(doi_parts[:6])

        data['filename'] = f'{file}_0001.mp3'
        data['target_path'] = (
            f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_AUDIO_BASE_DIR", "")}'
            f'{main_dir}/{file}_0001.mp3'
        )
        data['thumbnail_path'] = (
            f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_AUDIO_BASE_DIR", "")}'
            f'{main_dir}/{file}_0001.jpg'
        )

    return data


def make_ordinal(n):
    """
    Converts an integer into its ordinal representation.

    Examples::
        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'

    Args:
        n: Integer-like value.

    Returns:
        str: Ordinal form of ``n``.
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def get_mime_category(extension):
    """
    Returns a primary type category inferred from a file extension.

    Args:
        extension: File extension without dot (e.g. "mp4", "jpg", "pdf").

    Returns:
        str: One of "Moving Image", "Audio", "Still Image", "Textual", "Unknown".
    """
    mime, _ = mimetypes.guess_type("file." + extension)
    if mime:
        if mime.startswith("video/"):
            return "Moving Image"
        elif mime.startswith("audio/"):
            return "Audio"
        elif mime.startswith("image/"):
            return "Still Image"
        elif mime.startswith("application/") or mime.startswith("text/"):
            return "Textual"
    return "Unknown"


def get_archival_unit(fonds, subfonds, series):
    """
    Retrieves an archival unit by fonds/subfonds/series numeric identifiers.

    Args:
        fonds: Fonds number.
        subfonds: Subfonds number.
        series: Series number.

    Returns:
        ArchivalUnit: Matching archival unit.

    Raises:
        ValidationError: If no matching archival unit exists.
    """
    try:
        return ArchivalUnit.objects.get(fonds=fonds, subfonds=subfonds, series=series)
    except ObjectDoesNotExist:
        raise ValidationError({'error': 'No Archival Unit exists with these specifications'})


def get_container(archival_unit, container_no):
    """
    Retrieves a container record by archival unit and container number.

    Args:
        archival_unit: Parent archival unit.
        container_no: Container number within the unit.

    Returns:
        Container: Matching container.

    Raises:
        ValidationError: If no matching container exists.
    """
    try:
        return Container.objects.get(archival_unit=archival_unit, container_no=container_no)
    except ObjectDoesNotExist:
        raise ValidationError({'error': 'No Container record exists with these specifications'})


def get_finding_aids_entity(container, folder_no, sequence_no):
    """
    Retrieves a finding aids entity by container + folder + sequence.

    Args:
        container: Parent container.
        folder_no: Folder number.
        sequence_no: Sequence number (0 for folder-level records).

    Returns:
        FindingAidsEntity: Matching finding aids entity.

    Raises:
        ValidationError: If no matching record exists.
    """
    try:
        return FindingAidsEntity.objects.get(
            container=container, folder_no=folder_no, sequence_no=sequence_no
        )
    except ObjectDoesNotExist:
        raise ValidationError({'error': 'No Folder / Item record exists with these specifications'})


def get_doi(doi):
    """
    Normalizes a DOI-like identifier by removing page/supplement suffixes.

    The incoming identifier may include page references (e.g. _P001) or
    special suffixes. This function returns the base digital object identifier
    used for DigitalVersion identifiers.

    Args:
        doi: DOI-like string (without extension).

    Returns:
        str: Normalized identifier.
    """
    digital_object_identifier = doi
    parts = doi.split("_")

    # HU_OSA_386_1_1_0001_0001_P001
    if len(parts) == 8:
        if "P" in doi:
            digital_object_identifier = '_'.join(parts[:7])

    # HU_OSA_386_1_1_0001_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_P001_A
    elif len(parts) == 9:
        if 'P' in parts[7]:
            digital_object_identifier = '_'.join(parts[:7])
        elif 'P' in parts[8]:
            digital_object_identifier = '_'.join(parts[:8])

    return digital_object_identifier


def get_label(doi):
    """
    Derives a human-readable label for page-based identifiers.

    Used to label access copies such as page images/derivatives.

    Args:
        doi: DOI-like string (without extension).

    Returns:
        str or None: A label like "Front Page" or "Page 12", or None if not applicable.
    """
    parts = doi.split("_")
    label = None

    # HU_OSA_386_1_1_0001_0001_P001
    if len(parts) == 8:
        page = int(parts[7][1:])
        if "P" in doi:
            if page == 0:
                label = 'Front Page'
            else:
                page = f"{int(parts[7][1:])}"
                label = f'Page {page}'

    # HU_OSA_386_1_1_0001_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_P001_A
    elif len(parts) == 9:
        if 'P' in parts[7]:
            page = f"{int(parts[7][1:])}/{parts[8]}"
        elif 'P' in parts[8]:
            page = int(parts[8][1:])

        if page == 0:
            label = 'Front Page'
        else:
            label = f'Page {page}'

    return label


def resolve_archival_unit_or_container(doi):
    """
    Resolves a DOI-like identifier into archival objects.

    Based on identifier shape, resolves:
        - archival unit
        - container
        - optionally a finding aids folder/item record
        - derived level indicator (container/folder/item)

    Args:
        doi: DOI-like identifier (without extension).

    Returns:
        dict: Keys:
            - archival_unit (ArchivalUnit or None)
            - container (Container or None)
            - finding_aids_entity (FindingAidsEntity or None)
            - level (str or None)

    Raises:
        ValidationError: If the identifier refers to non-existent objects.
    """
    container = None
    archival_unit = None
    level = None
    finding_aids_entity = None

    parts = doi.split("_")

    # HU_OSA_11112222
    if len(parts) == 3:
        try:
            container = Container.objects.get(barcode=doi)
            archival_unit = container.archival_unit
            level = 'container'
        except ObjectDoesNotExist:
            raise ValidationError({'error': 'No container exists with this barcode'})

    # HU_OSA_386_1_1_0001
    elif len(parts) == 6:
        archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
        container = get_container(archival_unit, int(parts[5]))
        level = 'container'

    # HU_OSA_386_1_1_0001_0001
    elif len(parts) == 7:
        archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
        container = get_container(archival_unit, int(parts[5]))
        finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), 0)
        level = 'folder'

    # HU_OSA_386_1_1_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_0001
    elif len(parts) == 8:
        archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
        container = get_container(archival_unit, int(parts[5]))

        if "P" in doi:
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), 0)
            level = "folder"
        else:
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), int(parts[7]))
            level = 'item'

    # HU_OSA_386_1_1_0001_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_P001_A
    elif len(parts) == 9:
        if 'P' in parts[7]:
            archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
            container = get_container(archival_unit, int(parts[5]))
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), 0)
            level = 'folder'
        elif 'P' in parts[8]:
            archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
            container = get_container(archival_unit, int(parts[5]))
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), int(parts[7]))
            level = 'item'
        else:
            pass

    return {
        'archival_unit': archival_unit,
        'container': container,
        'finding_aids_entity': finding_aids_entity,
        'level': level
    }


def get_research_cloud_path(access_copy_file):
    path = ""
    parts = access_copy_file.split("_")

    # HU_OSA_11112222
    if len(parts) == 3:
        pass

    # HU_OSA_386_1_1_0001
    elif len(parts) == 6:
        if parts[3] == '0':
            path = f"HU OSA {parts[2]}/HU OSA {parts[2]}-0-{parts[4]}/"
        else:
            path = f"HU OSA {parts[2]}/HU OSA {parts[2]}-{parts[3]}/HU OSA {parts[2]}-{parts[3]}-{parts[4]}/"

    # HU_OSA_386_1_1_0001_0001
    elif len(parts) == 7:
        if parts[3] == '0':
            path = f"HU OSA {parts[2]}/HU OSA {parts[2]}-0-{parts[4]}/"
        else:
            path = f"HU OSA {parts[2]}/HU OSA {parts[2]}-{parts[3]}/HU OSA {parts[2]}-{parts[3]}-{parts[4]}/"

    else:
        pass

    return f'{path}{access_copy_file}'


class DigitalObjectInfo(APIView):
    """
    Resolves an access copy filename into catalog metadata and delivery targets.

    GET accepts an access copy filename (including extension), validates the naming
    pattern, resolves the referenced archival objects, and returns:
        - DOI (normalized where applicable)
        - inferred or record-based primary type
        - hierarchy info (fonds/subfonds/series)
        - delivery target information (server and paths)

    Authentication / Authorization:
        - BearerAuthentication or SessionAuthentication
        - Restricted to users in the ``Api`` group via APIGroupPermission
    """

    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(responses={
        200: DigitalObjectInfoResponseSerializer(),
        400: 'Invalid filename'
    })
    def get(self, request, access_copy_file):
        """
        Returns metadata and upload targets for a given access copy filename.

        Args:
            request: DRF request.
            access_copy_file: Filename including extension.

        Returns:
            200 OK with DigitalObjectInfoResponse-like payload, or 400 on invalid filename.
        """
        if matches_any_pattern(access_copy_file):
            doi, _, extension = access_copy_file.rpartition(".")

            resolved_object = resolve_archival_unit_or_container(doi)

            # Determine primary type (prefer finding aids record when available)
            if resolved_object['finding_aids_entity']:
                primary_type = resolved_object['finding_aids_entity'].primary_type.type
            else:
                primary_type = get_mime_category(extension)

            if resolved_object['archival_unit'] and resolved_object['level']:
                archival_unit = resolved_object['archival_unit']
                container = resolved_object['container']

                response = {
                    'doi': get_doi(doi),
                    'primary_type': primary_type,
                    'level': resolved_object['level'],
                    'archival_unit': {
                        'fonds': {
                            'reference_number': archival_unit.parent.parent.reference_code,
                            'title': archival_unit.parent.parent.title,
                            'catalog_id': (
                                f"https://catalog.archivum.org/catalog/"
                                f"{archival_unit.parent.parent.isad.catalog_id}"
                            ) if hasattr(archival_unit.parent.parent, "isad") else "",
                        },
                        'subfonds': {
                            'reference_number': archival_unit.parent.reference_code,
                            'title': archival_unit.parent.title,
                            'catalog_id': (
                                f"https://catalog.archivum.org/catalog/"
                                f"{archival_unit.parent.isad.catalog_id}"
                            ) if hasattr(archival_unit.parent, "isad") else "",
                        },
                        'series': {
                            'reference_number': archival_unit.reference_code,
                            'title': archival_unit.title,
                            'catalog_id': (
                                f"https://catalog.archivum.org/catalog/"
                                f"{archival_unit.isad.catalog_id}"
                            ) if hasattr(archival_unit, "isad") else "",
                        }
                    },
                    'access_copy_to_catalog': get_access_copy_actions(doi, primary_type)
                }

                fa_entity = resolved_object['finding_aids_entity']
                if fa_entity:
                    response['reference_code'] = fa_entity.archival_reference_code
                    response['title'] = fa_entity.title
                    response['catalog_id'] = f"https://catalog.archivum.org/catalog/{fa_entity.catalog_id}"
                else:
                    response['reference_code'] = f"{archival_unit.reference_code}:{container.container_no}"
                    response['title'] = f"{container.carrier_type.type} #{container.container_no}"
                    response['catalog_id'] = (
                        f"https://catalog.archivum.org/catalog/{archival_unit.isad.catalog_id}"
                        f"?tab=content&start={container.container_no}"
                    )

                return Response(response, status=200)

        return Response({'error': 'Invalid filename'}, status=400)


class DigitalObjectUpsert(APIView):
    """
    Creates or updates a DigitalVersion record for a given access copy filename.

    POST accepts:
        - level: 'access' or 'master' (maps to DigitalVersion.level 'A' or 'M')
        - access_copy_file: access copy filename including extension

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

    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(responses={
        200: DigitalObjectUpsertResponseSerializer(),
        400: 'Invalid filename'
    })
    def post(self, request, level, access_copy_file):
        """
        Upserts a DigitalVersion record derived from the access copy filename.

        Args:
            request: DRF request.
            level: Either 'access' or 'master'.
            access_copy_file: Filename including extension.

        Returns:
            200 OK with the created/updated DigitalVersion id and filename,
            or 400 BAD REQUEST on invalid filename.
        """
        if matches_any_pattern(access_copy_file):
            doi, _, extension = access_copy_file.rpartition(".")
            resolved_object = resolve_archival_unit_or_container(doi)

            primary_type = (
                resolved_object['finding_aids_entity'].primary_type.type
                if resolved_object['finding_aids_entity'] else 'Moving Image'
            )
            access_copy = get_access_copy_actions(doi, primary_type)
            label = get_label(doi)

            if resolved_object['finding_aids_entity']:
                dv, created = DigitalVersion.objects.get_or_create(
                    finding_aids_entity=resolved_object['finding_aids_entity'],
                    identifier=get_doi(doi),
                    level='A' if level == 'access' else 'M',
                    label=label,
                    # digital_collection=resolved_object['finding_aids_entity'].archival_unit.title,
                    filename=access_copy['filename'],
                    available_online=True
                )
            else:
                dv, created = DigitalVersion.objects.get_or_create(
                    container=resolved_object['container'],
                    identifier=get_doi(doi),
                    level='A' if level == 'access' else 'M',
                    # NOTE: Existing code referenced finding_aids_entity when absent; preserved intent below.
                    # digital_collection=resolved_object['container'].archival_unit.title_full,
                    filename=access_copy['filename'],
                    available_online=True
                )

            # Publish the linked finding aids entity when present.
            if dv.finding_aids_entity_id:
                dv.finding_aids_entity.published = True
                dv.finding_aids_entity.save()

            return Response({
                'digital_version_id': dv.id,
                'filename': dv.filename,
            }, status=200)

        return Response({'error': 'Invalid filename'}, status=400)


class DigitalObjectRCUpsert(APIView):
    """
    Creates or updates a DigitalVersion record for a research cloud access copy filename.

    POST accepts:
        - access_copy_file: access copy filename including extension

    The endpoint:
        - validates filename pattern
        - resolves archival unit/container/finding aids entity
        - computes a normalized identifier and optional label
        - inserts the research cloud path
        - upserts a DigitalVersion record marked as available in research cloud
        - publishes the linked finding aids entity (if present)

    Authentication / Authorization:
        - BearerAuthentication or SessionAuthentication
        - Restricted to users in the ``Api`` group via APIGroupPermission
    """

    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(responses={
        200: DigitalObjectUpsertResponseSerializer(),
        400: 'Invalid filename'
    })
    def post(self, request, access_copy_file):
        """
        Upserts a DigitalVersion record derived from the access copy filename.

        Args:
            request: DRF request.
            access_copy_file: Filename including extension.

        Returns:
            200 OK with the created/updated DigitalVersion id and filename,
            or 400 BAD REQUEST on invalid filename.
        """
        if matches_any_pattern(access_copy_file):
            doi, _, extension = access_copy_file.rpartition(".")
            resolved_object = resolve_archival_unit_or_container(doi)

            if resolved_object['finding_aids_entity']:
                dv, created = DigitalVersion.objects.get_or_create(
                    finding_aids_entity=resolved_object['finding_aids_entity'],
                    identifier=doi,
                    level='A',
                    filename=access_copy_file,
                    available_research_cloud=True,
                    research_cloud_path=get_research_cloud_path(access_copy_file)
                )
            else:
                dv, created = DigitalVersion.objects.get_or_create(
                    container=resolved_object['container'],
                    identifier=doi,
                    level='A',
                    filename=access_copy_file,
                    available_research_cloud=True,
                    research_cloud_path=get_research_cloud_path(access_copy_file)
                )

            return Response({
                'digital_version_id': dv.id,
                'filename': dv.filename,
            }, status=200)

        return Response({'error': 'Invalid filename'}, status=400)
