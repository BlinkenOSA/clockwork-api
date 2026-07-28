import datetime
import json
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType
from digitization.models import DigitalVersion
from office365.runtime.client_request_exception import ClientRequestException
from research.models import Researcher, Request, RequestItem, RequestedMaterialsSharePointJob
from research.services.sharepoint_requested_materials import RequestedMaterialsSharePointService
from research.tasks import deliver_requested_materials_sharepoint_job
from research.views.requests_views import RequestLibraryMLR


class ResearchRequestsViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        super().setUp()
        self.researcher = Researcher.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            email='ada@example.com',
            status='approved',
        )
        self.request = Request.objects.create(researcher=self.researcher, request_date=datetime.datetime.now())

        fonds = ArchivalUnit.objects.create(fonds=1201, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1201,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1201,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            digital_version_exists=True,
            barcode='HU_OSA_REQ',
        )

    def test_request_item_status_step_next_with_digital_version(self):
        item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=self.container,
            status='2',
        )

        with patch('research.views.requests_views.EmailWithTemplate.send_request_delivered_user') as send_mail:
            response = self.client.put(
                reverse('research-v1:request-item-status-change', kwargs={'action': 'next', 'request_item_id': item.id})
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, '9')
        send_mail.assert_called_once()

    def test_request_item_status_step_previous(self):
        item = RequestItem.objects.create(
            request=self.request,
            item_origin='L',
            status='4',
        )

        response = self.client.put(
            reverse('research-v1:request-item-status-change', kwargs={'action': 'previous', 'request_item_id': item.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, '3')

    def test_requests_list_for_print_only_pending(self):
        RequestItem.objects.create(request=self.request, item_origin='L', status='2')
        RequestItem.objects.create(request=self.request, item_origin='L', status='5')

        response = self.client.get(reverse('research-v1:requests-list-for-print'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], '2')

    def test_digital_requests_list_only_returns_items_with_digital_containers(self):
        digital_item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=self.container,
        )
        plain_container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_REQ_NO_DIGITAL',
        )
        RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=plain_container,
        )
        RequestItem.objects.create(
            request=self.request,
            item_origin='L',
            status='2',
        )

        response = self.client.get(reverse('research-v1:requests-digital-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], digital_item.id)

    @patch('research.views.requests_views.deliver_requested_materials_sharepoint_job.delay')
    def test_request_requested_materials_sharepoint_creates_job(self, mocked_delay):
        mocked_delay.return_value = SimpleNamespace(id='celery-123')
        request_item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=self.container,
        )
        response = self.client.post(
            reverse(
                'research-v1:request-item-requested-materials-sharepoint',
                kwargs={'request_item_id': request_item.id}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mocked_delay.assert_called_once()
        job = RequestedMaterialsSharePointJob.objects.get(pk=response.data['id'])
        self.assertEqual(job.request_item, request_item)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.current_step, 'queued')
        self.assertEqual(job.celery_task_id, 'celery-123')
        self.assertEqual(response.data['request_item_id'], request_item.id)
        self.assertEqual(response.data['request_id'], self.request.id)

    def test_requested_materials_sharepoint_job_detail_returns_status(self):
        request_item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=self.container,
        )
        job = RequestedMaterialsSharePointJob.objects.create(
            request_item=request_item,
            status='running',
            current_step='copying_files',
            message='Copying files... (1/2)',
            progress_current=3,
            progress_total=5,
            celery_task_id='celery-123',
        )

        response = self.client.get(
            reverse(
                'research-v1:requested-materials-sharepoint-job-detail',
                kwargs={'pk': job.id}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'running')
        self.assertEqual(response.data['current_step'], 'copying_files')
        self.assertEqual(response.data['message'], 'Copying files... (1/2)')
        self.assertEqual(response.data['request_item_id'], request_item.id)
        self.assertEqual(response.data['progress_percent'], 60)


class RequestLibraryMLRHelperTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        self.view = RequestLibraryMLR()

    def test_get_locations_defaults_to_general_collection(self):
        items = [{'952': {'subfields': [{'a': 'x'}]}}]
        locations = self.view._get_locations(items)
        self.assertEqual(locations, {'General collection'})

    def test_get_collections_extracts_subfield_a(self):
        fields = [{'580': {'subfields': [{'a': 'Collection A'}, {'b': 'ignored'}]}}]
        collections = self.view._get_collections(fields)
        self.assertEqual(collections, {'Collection A'})


class RequestedMaterialsSharePointServiceTests(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        super().setUp()
        self.researcher = Researcher.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            email='ada.service@example.com',
            status='approved',
        )
        self.request = Request.objects.create(researcher=self.researcher, request_date=datetime.datetime.now())

        fonds = ArchivalUnit.objects.create(fonds=1202, level='F', title='Fonds Service')
        subfonds = ArchivalUnit.objects.create(
            fonds=1202,
            subfonds=1,
            level='SF',
            title='Subfonds Service',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1202,
            subfonds=1,
            series=1,
            level='S',
            title='Series Service',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_SERVICE_REQ',
        )
        self.request_item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=self.container,
        )
        self.service = RequestedMaterialsSharePointService()

    def test_get_eligible_digital_versions_filters_for_access_research_cloud_items(self):
        matching = DigitalVersion.objects.create(
            container=self.container,
            level='A',
            available_research_cloud=True,
            research_cloud_path='HU OSA 394/test-file.mp4',
        )
        DigitalVersion.objects.create(
            container=self.container,
            level='M',
            available_research_cloud=True,
            research_cloud_path='HU OSA 394/master-file.mov',
        )
        DigitalVersion.objects.create(
            container=self.container,
            level='A',
            available_research_cloud=False,
            research_cloud_path='HU OSA 394/not-available.mp4',
        )
        DigitalVersion.objects.create(
            container=self.container,
            level='A',
            available_research_cloud=True,
            research_cloud_path='',
        )

        digital_versions = list(self.service.get_eligible_digital_versions(self.request_item))

        self.assertEqual(digital_versions, [matching])

    @patch('research.services.sharepoint_requested_materials.EmailWithTemplate')
    @patch.object(RequestedMaterialsSharePointService, '_share_folder_with_researcher')
    @patch.object(RequestedMaterialsSharePointService, '_copy_file_to_requested_materials', return_value=True)
    @patch.object(RequestedMaterialsSharePointService, '_ensure_folder')
    @patch.object(RequestedMaterialsSharePointService, '_get_client_context')
    @patch.object(RequestedMaterialsSharePointService, '_get_research_cloud_file_info')
    def test_deliver_requested_materials_for_request_copies_shares_and_notifies(
            self,
            mocked_get_file_info,
            mocked_get_context,
            mocked_ensure_folder,
            mocked_copy_file,
            mocked_share_folder,
            mocked_mailer,
    ):
        matching = DigitalVersion.objects.create(
            container=self.container,
            level='A',
            available_research_cloud=True,
            research_cloud_path='HU OSA 394/test-file.mp4',
        )
        mocked_get_file_info.return_value = {
            'name': 'test-file.mp4',
            'server_relative_url': '/sites/osa-researchcloud/Shared Documents/HU OSA 394/test-file.mp4',
        }
        mocked_folder = type('FolderStub', (), {'properties': {'ServerRelativeUrl': '/sites/osa-researchcloud-requests/confidential/Lovelace, Ada'}})()
        mocked_ensure_folder.return_value = (mocked_folder, True)

        result = self.service.deliver_requested_materials_for_request_item(self.request_item)

        self.assertEqual(list(self.service.get_eligible_digital_versions(self.request_item)), [matching])
        self.assertEqual(mocked_get_context.call_count, 2)
        mocked_copy_file.assert_called_once()
        mocked_share_folder.assert_called_once_with(mocked_folder, self.researcher.email)
        mocked_mailer.assert_called_once()
        mail = mocked_mailer.return_value
        mail.send_requested_materials_shared_user.assert_called_once()
        mail.send_requested_materials_shared_admin.assert_called_once()
        self.assertEqual(result['copied_files'], ['test-file.mp4'])
        self.assertEqual(result['shared_with'], self.researcher.email)

    @patch.object(RequestedMaterialsSharePointService, '_get_client_context')
    @patch.object(RequestedMaterialsSharePointService, '_get_research_cloud_file_info', return_value=None)
    def test_deliver_requested_materials_for_request_returns_empty_result_when_no_file_exists(
            self, mocked_get_file_info, mocked_get_context
    ):
        DigitalVersion.objects.create(
            container=self.container,
            level='A',
            available_research_cloud=True,
            research_cloud_path='HU OSA 394/test-file.mp4',
        )

        result = self.service.deliver_requested_materials_for_request_item(self.request_item)

        mocked_get_file_info.assert_called_once()
        self.assertEqual(result['copied_files_count'], 0)
        self.assertEqual(result['available_files_count'], 0)
        self.assertEqual(mocked_get_context.call_count, 1)

    @patch.object(RequestedMaterialsSharePointService, '_copy_file_via_sharepoint_job')
    @patch.object(RequestedMaterialsSharePointService, '_destination_file_exists', return_value=False)
    def test_copy_file_to_requested_materials_uses_sharepoint_copy_job(
            self, mocked_destination_exists, mocked_copy_job
    ):
        source_ctx = SimpleNamespace()
        destination_ctx = SimpleNamespace()
        folder = SimpleNamespace(properties={'ServerRelativeUrl': '/sites/osa-researchcloud-requests/confidential/Lovelace, Ada'})
        file_info = {
            'name': 'large-file.mp4',
            'server_relative_url': '/sites/osa-researchcloud/Shared Documents/HU OSA 394/large-file.mp4',
        }

        copied = self.service._copy_file_to_requested_materials(source_ctx, destination_ctx, folder, file_info)

        self.assertTrue(copied)
        mocked_destination_exists.assert_called_once()
        mocked_copy_job.assert_called_once_with(
            source_ctx,
            destination_ctx,
            folder,
            file_info,
            '/sites/osa-researchcloud-requests/confidential/Lovelace, Ada/large-file.mp4',
            progress_callback=None,
        )


class RequestedMaterialsSharePointTaskTests(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        super().setUp()
        self.researcher = Researcher.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            email='ada.task@example.com',
            status='approved',
        )
        self.request = Request.objects.create(researcher=self.researcher, request_date=datetime.datetime.now())
        fonds = ArchivalUnit.objects.create(fonds=1301, level='F', title='Task Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1301,
            subfonds=1,
            level='SF',
            title='Task Subfonds',
            parent=fonds,
        )
        series = ArchivalUnit.objects.create(
            fonds=1301,
            subfonds=1,
            series=1,
            level='S',
            title='Task Series',
            parent=subfonds,
        )
        container = Container.objects.create(
            archival_unit=series,
            carrier_type=CarrierType.objects.first(),
            digital_version_exists=True,
            barcode='HU_OSA_TASK',
        )
        self.request_item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=container,
            status='2',
        )
        self.job = RequestedMaterialsSharePointJob.objects.create(
            request_item=self.request_item,
            status='pending',
            current_step='queued',
        )

    @patch('research.tasks.RequestedMaterialsSharePointService.deliver_requested_materials_for_request_item', return_value={})
    def test_successful_job_sets_request_item_status_to_uploaded(self, mocked_deliver):
        deliver_requested_materials_sharepoint_job(self.job.id)

        self.request_item.refresh_from_db()
        self.job.refresh_from_db()

        self.assertEqual(self.request_item.status, '9')
        self.assertEqual(self.job.status, 'completed')
        mocked_deliver.assert_called_once()
