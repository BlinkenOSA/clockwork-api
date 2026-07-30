import json
import os
import re
import tempfile
import time
from urllib.parse import urlsplit

from django.conf import settings
from django.db.models import Q
from office365.runtime.client_result import ClientResult
from office365.runtime.client_value_collection import ClientValueCollection
from office365.runtime.client_request_exception import ClientRequestException
from office365.runtime.queries.service_operation import ServiceOperationQuery
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.migration.copy_migration_options import CopyMigrationOptions
from office365.sharepoint.sharing.external_site_option import ExternalSharingSiteOption
from office365.sharepoint.sites.copy_migration_iInfo import CopyMigrationInfo

from clockwork_api.mailer.email_with_template import EmailWithTemplate
from digitization.models import DigitalVersion


class RequestedMaterialsSharePointError(Exception):
    pass


class SharePointCopyMigrationOptions(CopyMigrationOptions):
    @property
    def entity_type_name(self):
        return 'SP.CopyMigrationOptions'


class SharePointCopyMigrationInfo(CopyMigrationInfo):
    @property
    def entity_type_name(self):
        return 'SP.CopyMigrationInfo'


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
        source_ctx, available_files = self._get_available_source_files(request_item)

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
                source_ctx,
                requested_materials_ctx,
                folder,
                file_info,
                progress_callback=progress_callback,
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
        # Temporarily disabled: keep copied materials staff-only until researcher sharing is re-enabled.
        # self._report_progress(progress_callback, 'sharing_directory', 'Sharing directory...', 4)
        # self._share_folder_with_researcher(folder, request_obj.researcher.email)
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
            shared_with=None,
            notification_emails={
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

    def _get_available_source_files(self, request_item):
        if request_item.item_origin == 'FA':
            digital_versions = self.get_eligible_digital_versions(request_item)
            if not digital_versions:
                return None, []

            source_site_url = settings.SHAREPOINT_SITE
            source_ctx = self._get_client_context(source_site_url)
            return source_ctx, [
                file_info
                for file_info in (
                    self._get_sharepoint_file_info(
                        source_ctx,
                        settings.SHAREPOINT_DOCUMENT_LIBRARY,
                        digital_version.research_cloud_path,
                        source_site_url,
                    )
                    for digital_version in digital_versions
                )
                if file_info is not None
            ]

        if request_item.item_origin == 'FL' and request_item.identifier:
            source_site_url = settings.SHAREPOINT_FILM_LIBRARY
            source_ctx = self._get_client_context(source_site_url)
            file_info = self._get_sharepoint_file_info(
                source_ctx,
                settings.SHAREPOINT_FILM_LIBRARY_DOCUMENT_LIBRARY,
                '{0}.mp4'.format(request_item.identifier),
                source_site_url,
            )
            return source_ctx, [file_info] if file_info is not None else []

        return None, []

    def _get_client_context(self, site_url):
        cert_settings = {
            'client_id': settings.SHAREPOINT_CLIENT_ID,
            'thumbprint': settings.SHAREPOINT_THUMBPRINT,
            'cert_path': os.path.join(settings.BASE_DIR, 'selfsigncert.pem'),
            'scopes': ['{0}.default'.format(settings.SHAREPOINT_ROOT)],
        }
        return ClientContext(site_url).with_client_certificate(settings.SHAREPOINT_TENANT, **cert_settings)

    def _get_research_cloud_file_info(self, ctx, document_library, research_cloud_path):
        return self._get_sharepoint_file_info(ctx, document_library, research_cloud_path, settings.SHAREPOINT_SITE)

    def _get_sharepoint_file_info(self, ctx, document_library, file_path_value, source_site_url):
        if not file_path_value:
            return None

        file_path = self._build_server_relative_path(ctx, document_library, file_path_value)
        try:
            sp_file = ctx.web.get_file_by_server_relative_path(file_path).get().execute_query()
            return {
                'name': os.path.basename(file_path),
                'server_relative_url': sp_file.properties['ServerRelativeUrl'],
                'source_site_url': source_site_url,
            }
        except ClientRequestException as exc:
            if exc.response.status_code == 404:
                return None
            raise self._sharepoint_error(exc, 'checking_files')

    def _ensure_folder(self, ctx, document_library, folder_name):
        folder_path = self._build_server_relative_path(ctx, document_library, folder_name)
        try:
            return ctx.web.get_folder_by_server_relative_path(folder_path).get().execute_query(), False
        except ClientRequestException as exc:
            if exc.response.status_code != 404:
                raise self._sharepoint_error(exc, 'creating_directory')

        try:
            parent_folder = ctx.web.get_folder_by_server_relative_path(
                self._build_server_relative_path(ctx, document_library, '')
            )
            parent_folder.folders.add(folder_name).execute_query()
            return ctx.web.get_folder_by_server_relative_path(folder_path).get().execute_query(), True
        except ClientRequestException as exc:
            raise self._sharepoint_error(exc, 'creating_directory')

    def _copy_file_to_requested_materials(
            self,
            source_ctx,
            destination_ctx,
            folder,
            file_info,
            progress_callback=None,
    ):
        destination_file_path = '/'.join([folder.properties['ServerRelativeUrl'].rstrip('/'), file_info['name']])
        if self._destination_file_exists(destination_ctx, destination_file_path):
            return False

        try:
            self._copy_file_via_sharepoint_job(
                source_ctx,
                destination_ctx,
                folder,
                file_info,
                destination_file_path,
                progress_callback=progress_callback,
            )
            return True
        except ClientRequestException as exc:
            raise self._sharepoint_error(exc, 'copying_files')

    def _copy_file_via_sharepoint_job(
            self,
            source_ctx,
            destination_ctx,
            folder,
            file_info,
            destination_file_path,
            progress_callback=None,
    ):
        source_file_url = self._build_absolute_url(
            file_info.get('source_site_url', settings.SHAREPOINT_SITE),
            file_info['server_relative_url'],
        )
        destination_file_url = self._build_absolute_url(
            settings.SHAREPOINT_REQUESTED_MATERIALS,
            destination_file_path,
        )
        destination_folder_url = self._build_absolute_url(
            settings.SHAREPOINT_REQUESTED_MATERIALS,
            folder.properties['ServerRelativeUrl'],
        )
        self._report_progress(
            progress_callback,
            'copying_files',
            'Copying {0} to {1}'.format(file_info['name'], destination_file_url),
            3,
        )
        copy_job_info = self._create_copy_job(source_ctx, source_file_url, destination_folder_url)
        self._wait_for_copy_job(
            source_ctx,
            destination_ctx,
            destination_file_path,
            copy_job_info,
            progress_callback=progress_callback,
            file_name=file_info['name'],
            destination_file_url=destination_file_url,
        )

    def _create_copy_job(self, ctx, source_file_url, destination_folder_url):
        options = SharePointCopyMigrationOptions()
        return_type = ClientResult(ctx, ClientValueCollection(SharePointCopyMigrationInfo))
        payload = {
            'exportObjectUris': {
                'results': [source_file_url],
            },
            'destinationUri': destination_folder_url,
            'options': options,
        }
        qry = ServiceOperationQuery(
            ctx.site,
            'CreateCopyJobs',
            None,
            payload,
            None,
            return_type,
        )
        ctx.add_query(qry)
        return_type.execute_query()
        copy_jobs = return_type.value
        if len(copy_jobs) == 0:
            raise RequestedMaterialsSharePointError('copying_files: SharePoint did not return a copy job.')
        return copy_jobs[0]

    def _wait_for_copy_job(
            self,
            source_ctx,
            destination_ctx,
            destination_file_path,
            copy_job_info,
            progress_callback=None,
            file_name=None,
            destination_file_url=None,
            max_attempts=180,
            poll_interval_seconds=2,
    ):
        for _ in range(max_attempts):
            progress = source_ctx.site.get_copy_job_progress(copy_job_info).execute_query().value
            job_state = getattr(progress, 'JobState', None)
            logs = getattr(progress, 'Logs', None) or []

            if self._copy_job_logs_indicate_error(logs):
                raise RequestedMaterialsSharePointError(
                    'copying_files: SharePoint copy job failed for {0}. Logs: {1}'.format(
                        file_name or destination_file_path,
                        ' | '.join(str(log) for log in logs),
                    )
                )

            if self._destination_file_exists(destination_ctx, destination_file_path):
                return

            message = 'Copying files...'
            if job_state == 2:
                message = 'Copying files... (SharePoint job queued'
            elif job_state == 4:
                message = 'Copying files... (SharePoint job processing'

            if job_state in (2, 4):
                if file_name:
                    message = '{0}: {1})'.format(message, file_name)
                if destination_file_url:
                    message = '{0} -> {1}'.format(message, destination_file_url)
                self._report_progress(progress_callback, 'copying_files', message, 3)
                time.sleep(poll_interval_seconds)
                continue

            time.sleep(poll_interval_seconds)

        raise RequestedMaterialsSharePointError(
            'copying_files: SharePoint copy job timed out for {0}.'.format(file_name or destination_file_path)
        )

    def _copy_file_via_download_upload(self, source_ctx, destination_ctx, folder, file_info):
        source_file = source_ctx.web.get_file_by_server_relative_path(file_info['server_relative_url'])
        try:
            with tempfile.NamedTemporaryFile(mode='w+b') as temp_file:
                source_file.download_session(temp_file, chunk_size=10 * 1024 * 1024).execute_query()
                temp_file.flush()
                temp_file.seek(0)
                folder.files.create_upload_session(
                    temp_file,
                    chunk_size=10 * 1024 * 1024,
                    file_name=file_info['name'],
                ).execute_query()
        except ClientRequestException as exc:
            raise self._sharepoint_error(exc, 'copying_files')

    def _destination_file_exists(self, ctx, destination_file_path):
        try:
            ctx.web.get_file_by_server_relative_path(destination_file_path).get().execute_query()
            return True
        except ClientRequestException as exc:
            if exc.response.status_code == 404:
                return False
            raise self._sharepoint_error(exc, 'copying_files')

    def _share_folder_with_researcher(self, folder, researcher_email):
        try:
            folder.list_item_all_fields.share(
                researcher_email,
                share_option=ExternalSharingSiteOption.View,
                send_email=False,
            ).execute_query()
        except ClientRequestException as exc:
            raise self._sharepoint_error(exc, 'sharing_directory')

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
        # Temporarily disabled: do not email the researcher while SharePoint sharing is paused.
        # mail.send_requested_materials_shared_user()
        mail.send_requested_materials_shared_admin()

    def _build_server_relative_path(self, ctx, document_library, value):
        web_server_relative_url = self._get_web_server_relative_url(ctx).rstrip('/')
        normalized_library = document_library.strip('/')
        normalized_value = value.strip('/')

        base_path = '{0}/{1}'.format(web_server_relative_url, normalized_library)
        if not normalized_value:
            return base_path

        if normalized_value.startswith(normalized_library):
            return '{0}/{1}'.format(web_server_relative_url, normalized_value)
        return '{0}/{1}'.format(base_path, normalized_value)

    def _build_absolute_url(self, site_url, value):
        parsed_site = urlsplit(site_url)
        server_relative_value = self._normalize_server_relative_url(value)
        return '{0}://{1}{2}'.format(parsed_site.scheme, parsed_site.netloc, server_relative_value)

    def _normalize_server_relative_url(self, value):
        parsed_value = urlsplit(value)
        if parsed_value.scheme and parsed_value.netloc:
            return parsed_value.path
        if not value.startswith('/'):
            return '/{0}'.format(value)
        return value

    def _get_web_server_relative_url(self, ctx):
        server_relative_url = ctx.web.properties.get('ServerRelativeUrl')
        if server_relative_url is None:
            ctx.web.get().execute_query()
            server_relative_url = ctx.web.properties.get('ServerRelativeUrl', '')
        return server_relative_url.rstrip('/') or ''

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

    def _copy_job_logs_indicate_error(self, logs):
        error_markers = ('error', 'failed', 'exception')
        for log in logs:
            if any(marker in str(log).lower() for marker in error_markers):
                return True
        return False

    def _sharepoint_error(self, exc, stage):
        try:
            payload = json.loads(exc.response.text)
            code = payload.get('error', {}).get('code')
            message = payload.get('error', {}).get('message', {}).get('value')
            if code and message:
                return RequestedMaterialsSharePointError('{0}: {1} ({2})'.format(stage, message, code))
        except (TypeError, ValueError, AttributeError):
            pass
        return RequestedMaterialsSharePointError('{0}: {1}'.format(stage, exc.response.text))

    def _sanitize_folder_name(self, folder_name):
        return self.INVALID_FOLDER_CHARS_RE.sub('_', folder_name).strip()
