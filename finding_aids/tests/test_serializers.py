from django.test import TestCase

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import (
    FindingAidsEntityWriteSerializer,
    FindingAidsEntityReadSerializer,
)
from finding_aids.serializers.finding_aids_template_serializers import FindingAidsTemplateWriteSerializer


class FindingAidsSerializerTests(TestCase):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        fonds = ArchivalUnit.objects.create(fonds=900, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=900,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=900,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            container_no=1,
        )

    def test_entity_write_serializer_rejects_inverted_dates(self):
        serializer = FindingAidsEntityWriteSerializer(data={
            'archival_unit': self.series.id,
            'container': self.container.id,
            'folder_no': 1,
            'title': 'Test item',
            'date_from': '2021-01-01',
            'date_to': '2020-01-01',
            'primary_type': PrimaryType.objects.first().id,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_template_write_serializer_rejects_inverted_dates(self):
        serializer = FindingAidsTemplateWriteSerializer(data={
            'archival_unit': self.series.id,
            'is_template': True,
            'folder_no': 1,
            'title': 'Template',
            'date_from': '2021-01-01',
            'date_to': '2020-01-01',
            'primary_type': PrimaryType.objects.first().id,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_entity_read_serializer_container_title_and_container_flags(self):
        entity = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            title='Entity',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
        )
        data = FindingAidsEntityReadSerializer(entity).data

        self.assertEqual(data['container_title'], f"{self.container.carrier_type.type} #1")
        self.assertTrue('digital_version' in data['digital_version_exists_container'])

    def test_entity_read_serializer_template_has_empty_container_title(self):
        template = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            is_template=True,
            folder_no=1,
            title='Template',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
        )
        data = FindingAidsEntityReadSerializer(template).data

        self.assertEqual(data['container_title'], '')
        self.assertEqual(data['digital_version_exists_container'], {'digital_version': False})
