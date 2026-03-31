from django.test import TestCase

from accession.models import Accession, AccessionMethod
from accession.tests.helpers import make_accession_method, make_accession
from archival_unit.models import ArchivalUnit
from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types
from dashboard.serializers.log_serializers import (
    AccessionLogSerializer,
    ArchivalUnitLogSerializer,
    DigitizationLogSerializer,
)
from donor.tests.helpers import make_donor


class DashboardLogSerializerTests(TestCase):
    def setUp(self):
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types()
        self.container = make_container(self.series, self.carrier_type)

        self.method = make_accession_method()
        self.donor = make_donor()

        self.accession = make_accession(
            fonds=self.fonds,
            method=self.method,
            donor=self.donor
        )

    def test_accession_log_serializer(self):
        data = AccessionLogSerializer(self.accession).data
        self.assertEqual(data['id'], self.accession.id)
        self.assertEqual(data['archival_unit']['id'], self.fonds.id)

    def test_archival_unit_log_serializer(self):
        data = ArchivalUnitLogSerializer(self.series).data
        self.assertEqual(data['id'], self.series.id)
        self.assertEqual(data['reference_code'], self.series.reference_code)

    def test_digitization_log_serializer(self):
        data = DigitizationLogSerializer(self.container).data
        self.assertEqual(data['container_no'], f"{self.series.reference_code}:1")
