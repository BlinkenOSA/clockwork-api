from django.test import TestCase

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from digitization.serializers.container_serializers import (
    DigitizationContainerLogSerializer,
    DigitizationContainerDataSerializer,
)


TECH_MD = '{"streams":[{"codec_type":"video","duration":"905.0"}]}'


class DigitizationContainerSerializerTests(TestCase):
    fixtures = ['carrier_types']

    def setUp(self):
        fonds = ArchivalUnit.objects.create(fonds=700, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=700,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=700,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )

    def test_log_serializer_duration_and_reference_code(self):
        container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_1',
            digital_version_technical_metadata=TECH_MD,
        )

        data = DigitizationContainerLogSerializer(container).data
        self.assertEqual(data['container_no'], 'HU OSA 700-1-1:1')
        self.assertEqual(data['duration'], '00:15:05')

    def test_data_serializer_parses_json_or_false(self):
        with_md = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_2',
            digital_version_technical_metadata=TECH_MD,
        )
        without_md = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_3',
        )

        parsed = DigitizationContainerDataSerializer(with_md).data
        empty = DigitizationContainerDataSerializer(without_md).data

        self.assertEqual(parsed['digital_version_technical_metadata']['streams'][0]['codec_type'], 'video')
        self.assertFalse(empty['digital_version_technical_metadata'])
