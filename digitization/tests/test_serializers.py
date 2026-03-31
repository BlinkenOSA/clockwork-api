from unittest import skip

from django.test import TestCase

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types
from digitization.serializers.container_serializers import (
    DigitizationContainerLogSerializer,
    DigitizationContainerDataSerializer,
)
from digitization.tests.helpers import make_digital_version_container, get_tech_md


class DigitizationContainerSerializerTests(TestCase):
    def setUp(self):
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types(type='VHS')
        self.container = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
        )
        self.digital_version = make_digital_version_container(
            container=self.container,
            level='M',
            technical_metadata=get_tech_md(),
        )

    def test_log_serializer_duration_and_reference_code(self):
        data = DigitizationContainerLogSerializer(self.digital_version).data
        self.assertEqual(data['container_no'], 'HU OSA 206-3-1:1')
        self.assertEqual(data['duration'], '00:15:05')

    def test_data_serializer_parses_json_or_false(self):
        digital_version = make_digital_version_container(
            container=self.container,
        )

        parsed = DigitizationContainerDataSerializer(self.digital_version).data
        empty = DigitizationContainerDataSerializer(digital_version).data

        self.assertEqual(parsed['technical_metadata']['streams'][0]['codec_type'], 'video')
        self.assertFalse(empty['technical_metadata'])
