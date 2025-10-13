from django.contrib.auth.models import User
from django.test import TestCase
from hashids import Hashids

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType, AccessRight
from finding_aids.models import FindingAidsEntity


class FindingAidsTest(TestCase):
    """ Test module for FindingAids model """
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        self.fonds = ArchivalUnit.objects.create(
            fonds=206,
            level='F',
            title='Records of the Open Society Archives at Central European University'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=3,
            level='SF',
            title='Public Events',
            parent=self.fonds
        )
        self.series = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=3,
            series=1,
            level='S',
            title='Audiovisual Recordings of Public Events',
            parent=self.subfonds
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.get(pk=1),
            container_no=1
        )
        self.findings_aids_folder = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            primary_type=PrimaryType.objects.get(pk=1),
            title='Finding Aids test folder',
            date_from='2019-01-01'
        )
        self.findings_aids_item = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            description_level='L2',
            level='I',
            folder_no=1,
            sequence_no=1,
            primary_type=PrimaryType.objects.get(pk=1),
            title='Finding Aids test item',
            date_from='2019-01-01'
        )
        self.findings_aids_template = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            primary_type=PrimaryType.objects.get(pk=1),
            title='Finding Aids Template test record',
            date_from='2019-01-01',
            is_template=True
        )
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()

    def test_set_reference_code_folder(self):
        self.findings_aids_folder.set_reference_code()
        self.assertEqual(self.findings_aids_folder.archival_reference_code, 'HU OSA 206-3-1:1/1')

    def test_set_reference_code_item(self):
        self.findings_aids_item.set_reference_code()
        self.assertEqual(self.findings_aids_item.archival_reference_code, 'HU OSA 206-3-1:1/1-1')

    def test_set_reference_code_template(self):
        self.findings_aids_template.set_reference_code()
        self.assertEqual(self.findings_aids_template.archival_reference_code, 'HU OSA 206-3-1-TEMPLATE')

    def test_publish(self):
        self.findings_aids_folder.publish(self.user)
        self.assertTrue(self.findings_aids_folder.published)
        self.assertEqual(self.findings_aids_folder.user_published, self.user.username)

    def test_unpublish(self):
        self.findings_aids_folder.unpublish()
        self.assertFalse(self.findings_aids_folder.published)
        self.assertEqual(self.findings_aids_folder.user_published, "")

    def test_set_confidential(self):
        self.findings_aids_folder.set_confidential()
        self.assertTrue(self.findings_aids_folder.confidential)

    def test_set_non_confidential(self):
        self.findings_aids_folder.set_non_confidential()
        self.assertFalse(self.findings_aids_folder.confidential)

    def test_set_catalog_id(self):
        self.findings_aids_folder.set_catalog_id()
        hashids = Hashids(salt="blinkenosa", min_length=10)
        self.assertEqual(self.findings_aids_folder.catalog_id, hashids.encode(self.findings_aids_folder.id))
