from django.test import TestCase

from accession.models import Accession, AccessionMethod
from archival_unit.models import ArchivalUnit
from dashboard.serializers.log_serializers import (
    AccessionLogSerializer,
    ArchivalUnitLogSerializer,
    DigitizationLogSerializer,
)
from donor.models import Donor
from authority.models import Country
from container.models import Container
from controlled_list.models import CarrierType


class DashboardLogSerializerTests(TestCase):
    def setUp(self):
        self.fonds = ArchivalUnit.objects.create(
            fonds=100,
            level='F',
            title='Test Fonds'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=100,
            subfonds=1,
            level='SF',
            title='Test Subfonds',
            parent=self.fonds
        )
        self.series = ArchivalUnit.objects.create(
            fonds=100,
            subfonds=1,
            series=1,
            level='S',
            title='Test Series',
            parent=self.subfonds
        )

        self.method = AccessionMethod.objects.create(method='Donation')
        self.country = Country.objects.create(alpha3='USA', country='United States')
        self.donor = Donor.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            postal_code='12345',
            country=self.country,
            city='NYC',
            address='1 Main St'
        )

    def test_accession_log_serializer(self):
        accession = Accession.objects.create(
            title='Test Accession',
            transfer_date='2020-01-01',
            method=self.method,
            donor=self.donor,
            archival_unit=self.fonds
        )
        data = AccessionLogSerializer(accession).data
        self.assertEqual(data['id'], accession.id)
        self.assertEqual(data['archival_unit']['id'], self.fonds.id)

    def test_archival_unit_log_serializer(self):
        data = ArchivalUnitLogSerializer(self.series).data
        self.assertEqual(data['id'], self.series.id)
        self.assertEqual(data['reference_code'], self.series.reference_code)

    def test_digitization_log_serializer(self):
        carrier = CarrierType.objects.create(type='Box', width=10)
        container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=carrier,
            container_no=1
        )
        data = DigitizationLogSerializer(container).data
        self.assertEqual(data['container_no'], f"{self.series.reference_code}:1")
