from django.test import TestCase

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from container.serializers import ContainerSelectSerializer
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types, get_tech_md


class ContainerSelectSerializerTest(TestCase):
    """ Test module for ContainerSelectSerializer """
    def setUp(self):
        self.carrier_type = make_carrier_types()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.container = make_container(self.series, self.carrier_type)

    def test_reference_code(self):
        serializer = ContainerSelectSerializer(instance=self.container)
        data = serializer.data
        self.assertEqual(data['reference_code'], 'HU OSA 206-3-1:1')

    def test_digital_version_duration(self):
        container = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            digital_version_technical_metadata=get_tech_md())
        serializer = ContainerSelectSerializer(instance=container)
        data = serializer.data
        self.assertEqual(data['digital_version_duration'], '00:15:05')

    def test_digital_version_duration_none_when_missing(self):
        container = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            container_no=2
        )
        serializer = ContainerSelectSerializer(instance=container)
        data = serializer.data
        self.assertIsNone(data['digital_version_duration'])
