import csv
import os

from django.core.management import BaseCommand
from archival_unit.models import ArchivalUnit
from container.models import Container
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fonds', dest='fonds', help='Fonds')
        parser.add_argument('--subfonds', dest='subfonds', help='Fonds')
        parser.add_argument('--series', dest='series', help='Fonds')
        parser.add_argument('--file', help='File name')
        parser.add_argument('--collection', help='Digital collection name')

    def handle(self, *args, **options):
        fonds = options.get('fonds')
        subfonds = options.get('subfonds')
        series = options.get('series')
        file = options.get('file')
        collection = options.get('collection')

        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', file)

        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            archival_unit = ArchivalUnit.objects.get(fonds=fonds, subfonds=subfonds, series=series)

            for row in reader:
                box = int(row['Box'])
                folder = int(row['Folder'])
                sequence = int(row['FolderSequence'])
                date = row['Date']
                identifier = row['FileName v1 - FolderSequence'].replace('.pdf', '')

                # Get container record
                container, created = Container.objects.get_or_create(
                    archival_unit=archival_unit,
                    container_no=box
                )

                finding_aids_entity, fa_created = FindingAidsEntity.objects.get_or_create(
                    archival_unit=archival_unit,
                    container=container,
                    folder_no=folder,
                    sequence_no=sequence,
                    title=collection,
                    date_from=date,
                    description_level='L2',
                    level='I',
                    published=True,
                    user_created='jozsef.bone',
                    user_published='jozsef.bone'
                )
                print("Created: %s" % finding_aids_entity.archival_reference_code)
                
                # Digital Version
                digital_version, dv_created = DigitalVersion.objects.get_or_create(
                    finding_aids_entity=finding_aids_entity,
                    container=container,
                    identifier=identifier,
                    level='A',
                    digital_collection=collection,
                    filename=row['FileName v1 - FolderSequence'],
                    available_online=True
                )
                finding_aids_entity.save()

        # Unpublish the old ones
        for fa_entity in FindingAidsEntity.objects.filter(
            archival_unit=archival_unit,
            description_level='L1'
        ).all():
            fa_entity.unpublish()
            print("Unpublished: %s" % fa_entity.archival_reference_code)