import os
import re

from django.conf import settings
from django.db.models import Q
from office365.runtime.client_request_exception import ClientRequestException
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.sharing.external_site_option import ExternalSharingSiteOption
from office365.sharepoint.utilities.move_copy_util import MoveCopyUtil

from clockwork_api.mailer.email_with_template import EmailWithTemplate
from digitization.models import DigitalVersion


class RequestedMaterialsSharePointError(Exception):
    pass


class RequestedMaterialsSharePointService:
    """
    Delivers Research Cloud files into the requested-materials SharePoint site.
    """

    INVALID_FOLDER_CHARS_RE = re.compile(r'[\"*:<>?/\\\\|]')

    def deliver_requested_materials_for_request_item(self, request_item, progress_callback=None):
        request_obj = request_item.request

        if not request_obj.researcher.email:
            raise RequestedMaterialsSharePointError('Researcher email address is missing.')

        self._report_progress(progress_callback, 'checking_files', 'Checking files...', 1)
        digital_versions = self.get_eligible_digital_versions(request_item)
        if not digital_versions:
            return self._build_result()

        research_cloud_ctx = self._get_client_context(settings.SHAREPOINT_SITE)
        available_files = [
            file_info
            for file_info in (
                self._get_research_cloud_file_info(
                    research_cloud_ctx,
                    settings.SHAREPOINT_DOCUMENT_LIBRARY,
                    digital_version.research_cloud_path,
                )
                for digital_version in digital_versions
            )
            if file_info is not None
        ]

        if not available_files:
            return self._build_result()

        requested_materials_ctx = self._get_client_context(settings.SHAREPOINT_REQUESTED_MATERIALS)
        folder_name = self._sanitize_folder_name(request_obj.researcher.name)
        self._report_progress(progress_callback, 'creating_directory', 'Creating directory...', 2)
        folder, folder_created = self._ensure_folder(
            requested_materials_ctx,
            settings.SHAREPOINT_REQUESTED_MATERIALS_DOCUMENT_LIBRARY,
            folder_name,
        )

        copied_files = []
        existing_files = []
        self._report_progress(progress_callback, 'copying_files', 'Copying files...', 3)
        for file_info in available_files:
            copied = self._copy_file_to_requested_materials(
                research_cloud_ctx,
                requested_materials_ctx,
                folder,
                file_info,
            )
            if copied:
                copied_files.append(file_info['name'])
            else:
                existing_files.append(file_info['name'])
            self._report_progress(
                progress_callback,
                'copying_files',
                'Copying files... ({0}/{1})'.format(len(copied_files) + len(existing_files), len(available_files)),
                3,
            )

        folder_url = self._build_absolute_url(
            settings.SHAREPOINT_REQUESTED_MATERIALS,
            folder.properties['ServerRelativeUrl'],
        )
        self._report_progress(progress_callback, 'sharing_directory', 'Sharing directory...', 4)
        self._share_folder_with_researcher(folder, request_obj.researcher.email)
        self._report_progress(progress_callback, 'sending_emails', 'Sending emails...', 5)
        self._send_notifications(
            request_obj,
            folder_url,
            copied_files or existing_files,
        )

        return self._build_result(
            folder_created=folder_created,
            folder_url=folder_url,
            available_files=[file_info['name'] for file_info in available_files],
            copied_files=copied_files,
            existing_files=existing_files,
            shared_with=request_obj.researcher.email,
            notification_emails={
                'researcher': request_obj.researcher.email,
                'staff': list(getattr(settings, 'RESEARCH_ROOM_STAFF_EMAIL')),
            },
        )

    def get_eligible_digital_versions(self, request_item):
        if request_item.item_origin != 'FA' or not request_item.container_id:
            return DigitalVersion.objects.none()

        return DigitalVersion.objects.filter(
            Q(container_id=request_item.container_id) | Q(finding_aids_entity__container_id=request_item.container_id),
            level='A',
            available_research_cloud=True,
        ).exclude(
            research_cloud_path__isnull=True
        ).exclude(
            research_cloud_path__exact=''
        ).distinct()

    def _get_client_context(self, site_url):
        cert_settings = {
            'client_id': settings.SHAREPOINT_CLIENT_ID,
            'thumbprint': settings.SHAREPOINT_THUMBPRINT,
            'cert_path': os.path.join(settings.BASE_DIR, 'selfsigncert.pem'),
            'scopes': ['{0}.default'.format(settings.SHAREPOINT_ROOT)],
        }
        return ClientContext(site_url).with_client_certificate(settings.SHAREPOINT_TENANT, **cert_settings)

    def _get_research_cloud_file_info(self, ctx, document_library, research_cloud_path):
        if not research_cloud_path:
            return None

        file_path = self._build_server_relative_path(document_library, research_cloud_path)
        try:
            sp_file = ctx.web.get_file_by_server_relative_path(file_path).get().execute_query()
            return {
                'name': os.path.basename(file_path),
                'server_relative_url': sp_file.properties['ServerRelativeUrl'],
            }
        except ClientRequestException as exc:
            if exc.response.status_code == 404:
                return None
            raise RequestedMaterialsSharePointError(exc.response.text)

    def _ensure_folder(self, ctx, document_library, folder_name):
        folder_path = self._build_server_relative_path(document_library, folder_name)
        try:
            return ctx.web.get_folder_by_server_relative_path(folder_path).get().execute_query(), False
        except ClientRequestException as exc:
            if exc.response.status_code != 404:
                raise RequestedMaterialsSharePointError(exc.response.text)

        try:
            parent_folder = ctx.web.get_folder_by_server_relative_path(document_library)
            parent_folder.folders.add(folder_name).execute_query()
            return ctx.web.get_folder_by_server_relative_path(folder_path).get().execute_query(), True
        except ClientRequestException as exc:
            raise RequestedMaterialsSharePointError(exc.response.text)

    def _copy_file_to_requested_materials(self, source_ctx, destination_ctx, folder, file_info):
        destination_file_path = '/'.join([folder.properties['ServerRelativeUrl'].rstrip('/'), file_info['name']])
        if self._destination_file_exists(destination_ctx, destination_file_path):
            return False

        try:
            MoveCopyUtil.copy_file_by_path(
                source_ctx,
                file_info['server_relative_url'],
                self._build_absolute_url(settings.SHAREPOINT_REQUESTED_MATERIALS, destination_file_path),
                overwrite=False,
            )
            source_ctx.execute_query()
            return True
        except ClientRequestException as exc:
            raise RequestedMaterialsSharePointError(exc.response.text)

    def _destination_file_exists(self, ctx, destination_file_path):
        try:
            ctx.web.get_file_by_server_relative_path(destination_file_path).get().execute_query()
            return True
        except ClientRequestException as exc:
            if exc.response.status_code == 404:
                return False
            raise RequestedMaterialsSharePointError(exc.response.text)

    def _share_folder_with_researcher(self, folder, researcher_email):
        try:
            folder.list_item_all_fields.share(
                researcher_email,
                share_option=ExternalSharingSiteOption.View,
                send_email=False,
            ).execute_query()
        except ClientRequestException as exc:
            raise RequestedMaterialsSharePointError(exc.response.text)

    def _send_notifications(self, request_obj, folder_url, files):
        mail = EmailWithTemplate(
            researcher=request_obj.researcher,
            context={
                'researcher': request_obj.researcher,
                'request': request_obj,
                'folder_url': folder_url,
                'files': files,
            }
        )
        mail.send_requested_materials_shared_user()
        mail.send_requested_materials_shared_admin()

    def _build_server_relative_path(self, document_library, value):
        normalized_value = value.strip('/')
        if normalized_value.startswith(document_library):
            return normalized_value
        return '{0}/{1}'.format(document_library, normalized_value)

    def _build_absolute_url(self, site_url, value):
        normalized_site = site_url.rstrip('/')
        normalized_value = value.lstrip('/')
        return '{0}/{1}'.format(normalized_site, normalized_value)

    def _build_result(
            self,
            folder_created=False,
            folder_url=None,
            available_files=None,
            copied_files=None,
            existing_files=None,
            shared_with=None,
            notification_emails=None,
    ):
        available_files = available_files or []
        copied_files = copied_files or []
        existing_files = existing_files or []
        return {
            'requested_materials_folder_created': folder_created,
            'requested_materials_folder_url': folder_url,
            'available_files_count': len(available_files),
            'copied_files_count': len(copied_files),
            'existing_files_count': len(existing_files),
            'available_files': available_files,
            'copied_files': copied_files,
            'existing_files': existing_files,
            'shared_with': shared_with,
            'notification_emails': notification_emails or {},
        }

    def _report_progress(self, progress_callback, current_step, message, progress_current):
        if callable(progress_callback):
            progress_callback(current_step, message, progress_current)

    def _sanitize_folder_name(self, folder_name):
        return self.INVALID_FOLDER_CHARS_RE.sub('_', folder_name).strip()
