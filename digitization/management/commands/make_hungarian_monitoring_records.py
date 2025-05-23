import csv
import glob
import os

from django.core.management import BaseCommand
from django_date_extensions.fields import ApproximateDate

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity


class FindingAids:
    pass


class Command(BaseCommand):
    def handle(self, *args, **options):
        output_file = "HungarianMonitoring.csv"
        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', output_file)

        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            archival_unit = ArchivalUnit.objects.get(fonds=300, subfonds=40, series=8)

            for row in reader:
                box = int(row['Box'])
                folder = int(row['Folder'])
                sequence = int(row['FolderSequence'])
                date = row['Date']

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
                    title='Hungarian Monitoring',
                    date_from=date,
                    description_level='L2',
                    level='I',
                    published=True,
                    user_created='jozsef.bone',
                    user_published='jozsef.bone'
                )
                print("Created: %s" % finding_aids_entity.archival_reference_code)

        # Unpublish the old ones
        for fa_entity in FindingAidsEntity.objects.filter(
            archival_unit=archival_unit,
            description_level='L1'
        ).all():
            fa_entity.unpublish()
            print("Unpublished: %s" % fa_entity.archival_reference_code)