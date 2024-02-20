import csv
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('collection', help='Collection identifier')
        parser.add_argument('digital_collection', help='Digital collection name')

    def handle(self, *args, **options):
        collection = options.get('collection')
        digital_collection = options.get('digital_collection')

        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', '%s_datasheet.csv' % collection)

        with open(csv_file, newline='', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'fedora_id' in row:
                    uuid = row['fedora_id'].replace("osa:", "").replace("-", "")
                else:
                    uuid = None

                reference_code = row['reference_code']
                access_copy_id = row['access_copy']

                primary_type = row['primary_type']
                if primary_type == 'Audio':
                    filetype = 'mp3'
                if primary_type == 'Moving Image':
                    filetype = 'mp4'
                if primary_type == 'Textual':
                    filetype = 'pdf'

                try:
                    fa_entity = FindingAidsEntity.objects.get(archival_reference_code=reference_code)
                    if uuid:
                        fa_entity.uuid = uuid
                        fa_entity.save()

                    DigitalVersion.objects.get_or_create(
                        finding_aids_entity=fa_entity,
                        identifier=access_copy_id,
                        digital_collection=digital_collection,
                        level='A',
                        filename='%s.%s' % (access_copy_id, filetype),
                        available_online=True,
                    )
                    print("Added access copy: %s" % access_copy_id)
                except ObjectDoesNotExist:
                    print("Can't find the record: %s" % reference_code)