from django.test import TestCase

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from isad.models import Isad
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer
from workflow.serializers.container_serializers import ContainerDigitizedSerializer


class WorkflowSerializersTests(TestCase):
    fixtures = ['carrier_types']

    def setUp(self):
        fonds = ArchivalUnit.objects.create(fonds=300, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=300,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=300,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        Isad.objects.create(
            archival_unit=self.series,
            title=self.series.title,
            reference_code=self.series.reference_code,
            description_level='S',
            year_from=1900,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_WORK',
        )

    def test_archival_unit_workflow_serializer(self):
        data = ArchivalUnitSerializer(self.series).data
        self.assertEqual(data['fonds']['number'], 300)
        self.assertEqual(data['subfonds']['number'], 1)
        self.assertEqual(data['series']['number'], 1)

    def test_container_digitized_serializer(self):
        data = ContainerDigitizedSerializer(self.container).data
        self.assertEqual(data['container']['barcode'], 'HU_OSA_WORK')
        self.assertEqual(data['container']['carrier_type'], self.container.carrier_type.type)
        self.assertEqual(data['archival_unit']['series']['number'], 1)
