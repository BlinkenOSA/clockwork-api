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
        output_file = "RFEMonitoringPolish.csv"
        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', output_file)

        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            fieldnames = reader.fieldnames

        for row in rows:
            date = row['Date']
            year, month, day = date.split("-")
            approx_date = ApproximateDate(year=int(year), month=int(month), day=int(day))

            archival_unit = ArchivalUnit.objects.get(fonds=300, subfonds=50, series=16)
            container = Container.objects.get(archival_unit=archival_unit, container_no=int(row['Box']))
            finding_aids_records = FindingAidsEntity.objects.filter(
                container=container
            )

            for fa in finding_aids_records:
                if fa.date_to:
                    if approx_date >= fa.date_from and approx_date <= fa.date_to:
                        row['Folder'] = fa.folder_no
                        print("Added data to: %s" % row['Date'])
                else:
                    if approx_date == fa.date_from:
                        row['Folder'] = fa.folder_no
                        print("Added data to: %s" % row['Date'])

        # Step 3: Write back to file
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

