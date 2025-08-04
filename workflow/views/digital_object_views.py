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
from workflow.serializers.digital_object_serializers import DigitalObjectInfoResponseSerializer, \
    DigitalObjectUpsertResponseSerializer


def matches_any_pattern(s):
    patterns = [
        # HU_OSA_386_1_1_0001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}\.[a-zA-Z0-9]+$',

        # HU_OSA_386_1_1_0001_0001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}\.[a-zA-Z0-9]+$',

        # HU_OSA_386_1_1_0001_0001_P001
        r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_P\d{3}\.[a-zA-Z0-9]+$',

        # HU_OSA_384_0_2_0023_0001_P050_A - Special cases for the Bartok Colleciton
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
        data['target_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_TEXT_BASE_DIR", "")}{main_dir}/{sub_dir}/{filename}.pdf'
        data['thumbnail_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_TEXT_BASE_DIR", "")}{main_dir}/{sub_dir}/{filename}.jpg'
    elif primary_type == 'Still Image':
        data['target_server'] = getattr(settings, 'DIGITAL_OBJECTS_STORAGE_IMAGE_SERVER', '')
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
        data['target_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_VIDEO_BASE_DIR", "")}{main_dir}/{sub_dir}/{sub_dir}_0001.m3u8'
        data['thumbnail_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_VIDEO_BASE_DIR", "")}{main_dir}/{sub_dir}/{sub_dir}_0001.jpg'
    elif primary_type == 'Audio':
        data['target_server'] = getattr(settings, 'DIGITAL_OBJECTS_STORAGE_AUDIO_SERVER', '')
        main_dir = '_'.join(doi_parts[:5])
        if len(doi_parts) == 6:
            new_parts = doi_parts[:5] + ['0001']
            file = '_'.join(new_parts)
        else:
            file = '_'.join(doi_parts[:6])
        data['filename'] = f'{file}_0001.mp3'
        data['target_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_AUDIO_BASE_DIR", "")}{main_dir}/{file}_0001.mp3'
        data['thumbnail_path'] = f'{getattr(settings, "DIGITAL_OBJECTS_STORAGE_AUDIO_BASE_DIR", "")}{main_dir}/{file}_0001.jpg'
    return data


def make_ordinal(n):
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def get_mime_category(extension):
    """
    Return the mime category of a file based on its extension.
    """
    mime, _ = mimetypes.guess_type("file" + extension)
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
    try:
        archival_unit = ArchivalUnit.objects.get(fonds=fonds, subfonds=subfonds, series=series)
        return archival_unit
    except ObjectDoesNotExist:
        raise ValidationError({'error': 'No Archival Unit exists with these specifications'})


def get_container(archival_unit, container_no):
    try:
        container = Container.objects.get(archival_unit=archival_unit, container_no=container_no)
        return container
    except ObjectDoesNotExist:
        raise ValidationError({'error': 'No Container record exists with these specifications'})


def get_finding_aids_entity(container, folder_no, sequence_no):
    try:
        fa_entity = FindingAidsEntity.objects.get(
            container=container, folder_no=folder_no, sequence_no=sequence_no)
        return fa_entity
    except ObjectDoesNotExist:
        raise ValidationError({'error': 'No Folder / Item record exists with these specifications'})


def get_doi(doi):
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
    digital_object_identifier = doi
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
            level = 'container with barcode'
        except ObjectDoesNotExist:
            raise ValidationError({'error': 'No container exists with this barcode'})

    # HU_OSA_386_1_1_0001
    elif len(parts) == 6:
        archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
        container = get_container(archival_unit, int(parts[5]))
        level = 'container with archival reference number'

    # HU_OSA_386_1_1_0001_0001
    elif len(parts) == 7:
        archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
        container = get_container(archival_unit, int(parts[5]))
        finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), 0)
        level = (f"{make_ordinal(int(parts[6]))} folder in "
                 f"{make_ordinal(int(parts[5]))} container.")

    # HU_OSA_386_1_1_0001_0001_P001 or HU_OSA_386_1_1_0001_0001_0001
    elif len(parts) == 8:
        archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
        container = get_container(archival_unit, int(parts[5]))

        if "P" in doi:
            page = int(parts[7][1:])
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), 0)
            level = (f"{make_ordinal(page)} page in {make_ordinal(int(parts[6]))} folder in "
                     f"{make_ordinal(int(parts[5]))} container.")
        else:
            finding_aids_entity = get_finding_aids_entity(
                container, int(parts[6]), int(parts[7]))
            level = 'item with archival reference number'

    # HU_OSA_386_1_1_0001_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_P001_A
    elif len(parts) == 9:
        if 'P' in parts[7]:
            archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
            container = get_container(archival_unit, int(parts[5]))
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), 0)
            page = int(parts[7][1:])
            level = (f"{make_ordinal(page) if page != 0 else 'Front'} page of the "
                     f"{make_ordinal(int(parts[6]))} folder in the "
                     f"{make_ordinal(int(parts[5]))} container.")
        elif 'P' in parts[8]:
            archival_unit = get_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
            container = get_container(archival_unit, int(parts[5]))
            finding_aids_entity = get_finding_aids_entity(container, int(parts[6]), int(parts[7]))
            page = int(parts[8][1:])
            level = (f"{make_ordinal(page)} page of the "
                     f"{make_ordinal(int(parts[7]))} item in the "
                     f"{make_ordinal(int(parts[6]))} folder in the "
                     f"{make_ordinal(int(parts[5]))} container.")
        else:
            pass

    return {
        'archival_unit': archival_unit,
        'container': container,
        'finding_aids_entity': finding_aids_entity,
        'level': level
    }


class DigitalObjectInfo(APIView):
    """
    Get info about where to copy the access copies of a digital object.
    """
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(responses={
        200: DigitalObjectInfoResponseSerializer(),
        400: 'Invalid filename'
    })
    def get(self, request, access_copy_file):
        if matches_any_pattern(access_copy_file):
            doi, _, extension = access_copy_file.rpartition(".")

            resolved_object = resolve_archival_unit_or_container(doi)

            primary_type = resolved_object['finding_aids_entity'].primary_type.type \
                if resolved_object['finding_aids_entity'] else 'Moving Image'

            if resolved_object['archival_unit'] and resolved_object['level']:
                return Response({
                    'doi': get_doi(doi),
                    'container_reference_code': f'{resolved_object["archival_unit"].reference_code}:'
                                                f'{resolved_object["container"].container_no}',
                    'fa_entity_reference_code': resolved_object["finding_aids_entity"].archival_reference_code
                        if resolved_object["finding_aids_entity"] else 'N/A',
                    'primary_type': primary_type,
                    'catalog_id': resolved_object["finding_aids_entity"].catalog_id if resolved_object["finding_aids_entity"] else 'N/A',
                    'title': resolved_object["finding_aids_entity"].title if resolved_object["finding_aids_entity"] else 'N/A',
                    'level': resolved_object['level'],
                    'access_copy_to_catalog': get_access_copy_actions(doi, primary_type)
                }, status=200)
        else:
            return Response({'error': 'Invalid filename'}, status=400)


class DigitalObjectUpsert(APIView):
    """
        Create or update a Digital Object and give back the data. (level parameter is either 'access' or 'master')
    """
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    @swagger_auto_schema(responses={
        200: DigitalObjectUpsertResponseSerializer(),
        400: 'Invalid filename'
    })
    def post(self, request, level, access_copy_file):
        if matches_any_pattern(access_copy_file):
            doi, _, extension = access_copy_file.rpartition(".")
            resolved_object = resolve_archival_unit_or_container(doi)

            primary_type = resolved_object['finding_aids_entity'].primary_type.type \
                if resolved_object['finding_aids_entity'] else 'Moving Image'
            access_copy = get_access_copy_actions(doi, primary_type)

            label = get_label(doi)

            if resolved_object['finding_aids_entity']:
                dv, created = DigitalVersion.objects.get_or_create(
                    finding_aids_entity=resolved_object['finding_aids_entity'],
                    identifier=get_doi(doi),
                    level='A' if level == 'access' else 'M',
                    label=label,
                    digital_collection=resolved_object['finding_aids_entity'].archival_unit.title,
                    filename=access_copy['filename'],
                    available_online=True
                )
            else:
                dv, created = DigitalVersion.objects.get_or_create(
                    container=resolved_object['container'],
                    identifier=get_doi(doi),
                    level='A' if level == 'access' else 'M',
                    digital_collection=resolved_object['finding_aids_entity'].archival_unit.title_full,
                    filename=access_copy['filename'],
                    available_online=True
                )

            dv.finding_aids_entity.published = True
            dv.finding_aids_entity.save()

            return Response({
                'digital_version_id': dv.id,
                'filename': dv.filename,
            }, status=200)
        else:
            return Response({'error': 'Invalid filename'}, status=400)
