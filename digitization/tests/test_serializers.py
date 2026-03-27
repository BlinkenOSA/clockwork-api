from unittest import skip

from django.test import TestCase

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types
from digitization.serializers.container_serializers import (
    DigitizationContainerLogSerializer,
    DigitizationContainerDataSerializer,
)


TECH_MD = '{"streams":[{"codec_type":"video","duration":"905.0"}]}'


class DigitizationContainerSerializerTests(TestCase):
    def setUp(self):
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types(type='VHS')

    @skip
    def test_log_serializer_duration_and_reference_code(self):
        container = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            barcode='HU_OSA_1',
            digital_version_technical_metadata=TECH_MD,
        )

        data = DigitizationContainerLogSerializer(container).data
        self.assertEqual(data['container_no'], 'HU OSA 206-3-1:1')
        self.assertEqual(data['duration'], '00:15:05')

    @skip
    def test_data_serializer_parses_json_or_false(self):
        with_md = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            barcode='HU_OSA_2',
            digital_version_technical_metadata=TECH_MD,
        )
        without_md = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            barcode='HU_OSA_3',
        )

        parsed = DigitizationContainerDataSerializer(with_md).data
        empty = DigitizationContainerDataSerializer(without_md).data

        self.assertEqual(parsed['digital_version_technical_metadata']['streams'][0]['codec_type'], 'video')
        self.assertFalse(empty['digital_version_technical_metadata'])
