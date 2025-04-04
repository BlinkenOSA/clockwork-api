import csv
import os
import urllib

import requests
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import BaseCommand
from lxml import etree

from archival_unit.models import ArchivalUnit
from clockwork_api import settings
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity

FEDORA_URL = getattr(settings, "FEDORA_URL")
FEDORA_RISEARCH = '%s/risearch' % FEDORA_URL
FEDORA_ADMIN = getattr(settings, "FEDORA_ADMIN")
FEDORA_ADMIN_PASS = getattr(settings, "FEDORA_ADMIN_PASS")

COLLECTIONS = {
        'phr': '<info:fedora/osa:b9e6110d-b739-451a-bc67-c13cb3b382af>',
        'curph': '<info:fedora/osa:ea9bfcca-2dd5-4da8-b6a4-74871c5373f4>',
        'situation': '<info:fedora/osa:f80cb1e2-fb79-4068-af0f-80c7a39465cb>',
        'information-items': '<info:fedora/osa:484d852e-1334-4570-a2be-e41230b9e36a>',
        'background-reports': '<info:fedora/osa:6f4d954a-481d-4e85-af9c-5af1cebee9a9>',
        'hungarian-monitoring': '<info:fedora/osa:8971ff25-e237-4b40-8713-c375c7c37e71>',  # Hungarian Monitoring
        'soviet-tv': '<info:fedora/osa:ed645793-91bb-4168-9515-7a223fed242a>',  # SovietTV
        'hedervary': '<info:fedora/osa:693f36ae-56a5-4564-89ee-0bc7b20eb414>',  # Hedervary
        'szabo-miklos': '<info:fedora/osa:b28adc31-caee-417d-96d7-e418db6fdd1d>',  # SzaboMiklos
        'blinken-photos': '<info:fedora/osa:17dda84d-6b6c-4f7e-85f1-cd5cecb5aac0>',  # BlinkenPhotos
        'fec': '<info:fedora/osa:6401e666-ebee-4310-8f54-da0a7fb2aa0c>', # FEC
        'pue': '<info:fedora/osa:e0410998-f423-4efe-946b-751433c43594>',  # PUE
        'russian-radio': '<info:fedora/osa:89898864-78b7-4cf9-b4f7-aaf218f85599>',  # Russian Radio
        'pup': '<info:fedora/osa:e0410998-f423-4efe-946b-751433c43594>',  # PUP
        'samizdat-audio': '<info:fedora/osa:3df6be8a-38e2-4207-a587-e658c06ca3a9>',  # Samizdat Audio
        'anna-gereb': '<info:fedora/osa:7fb5608a-f2be-4136-88b5-514c90919fed>',  # Anna Gereb
        'arpad-ajtony': '<info:fedora/osa:897e1efd-30ef-4647-828b-eebb5bf5814f>',  # Arpad Ajtony
        'david-rhode': '<info:fedora/osa:9c84e128-1cad-48f6-8392-9985da5d23a0>',  # David Rhode
        'cultural-heritage': '<info:fedora/osa:5b926fec-e019-4e12-bc9b-7f3cf9fb6ae1>',  # Cultural Heritage
}

RI_QUERY = "select $pid $state \
            from    <#ri> \
            where   $object <fedora-model:state> $state \
            and     ($object <fedora-model:hasModel> <info:fedora/osa:cm-item-arc> \
            or      $object <fedora-model:hasModel> <info:fedora/osa:cm-item-lib>) \
            and     $object <dc:identifier> $pid \
            and     $object <fedora-view:lastModifiedDate> $date \
            and     $object <info:fedora/fedora-system:def/relations-external#isMemberOfCollection> "

NAMESPACE = {'osa': 'http://greenfield.osaarchivum.org/ns/item'}

unicode = str


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.pids = []
        self.current_xml = None
        self.collection = None
        self.helper_csv = {}
        self.csv = []

    def add_arguments(self, parser):
        parser.add_argument('collection', help='Collection identifier')

    def handle(self, *args, **options):
        self.collection = options.get('collection')
        collection_pid = COLLECTIONS.get(self.collection, None)

        # 0. Read helper CSV if needed
        if self.collection == 'information-items':
            self.read_helper_csv(self.collection)

        if collection_pid:
            self.get_pidlist(collection_pid)
            for pid in self.pids:
                item = {}

                # 1. Add PID
                item['fedora_id'] = pid

                # 2. Add Reference Code
                self.get_document(pid)
                reference_code = self.get_reference_code(pid)

                if reference_code:
                    item['reference_code'] = reference_code

                    try:
                        fa_entity = FindingAidsEntity.objects.get(
                            archival_reference_code=reference_code
                        )
                        did = "HU_OSA_%s_%s_%s_%04d_%04d" % (
                            fa_entity.archival_unit.fonds, fa_entity.archival_unit.subfonds, fa_entity.archival_unit.series,
                            fa_entity.container.container_no, fa_entity.folder_no
                        )
                        item['access_copy'] = did
                        item['primary_type'] = fa_entity.primary_type.type
                        main_directory = 'HU_OSA_%s_%s_%s' % (fa_entity.archival_unit.fonds, fa_entity.archival_unit.subfonds, fa_entity.archival_unit.series)
                        item['makedir'] = "mkdir -p %s" % did if fa_entity.primary_type.type == 'Moving Image' else ''
                        item['download_command'] = self.get_download_command(pid, did, main_directory, fa_entity.primary_type.type)
                        item['thumbnail_command'] = self.get_thumbnail_command(pid, did, main_directory, fa_entity.primary_type.type)
                        item['access_copy_command'] = self.get_access_copy_command(pid, did, main_directory, fa_entity.primary_type.type)
                    except ObjectDoesNotExist:
                        item['access_copy'] = 'N/A'

                    self.csv.append(item)
                    self.write_csv(self.collection)
                else:
                    print("Can't match reference code to record: %s" % pid)
        else:
            print('Wrong collection identifier!')

    def get_pidlist(self, collection):
        ri_query = RI_QUERY + collection
        query = FEDORA_RISEARCH + '?type=tuples&lang=itql&format=json&query=' + urllib.parse.quote_plus(ri_query)

        r = requests.get(query)
        if r.ok:
            response = r.json()
            self.pids = list(map(lambda x: x['pid'], response['results']))

    def get_document(self, pid):
        r = requests.get("%s/objects/%s/datastreams/ITEM-ARC-EN/content" % (FEDORA_URL, pid))
        r.encoding = 'UTF-8'
        if r.ok:
            self.current_xml = r.text

    def get_reference_code(self, pid):
        xml = etree.fromstring(self.current_xml)
        arn = xml.xpath('//osa:archivalReferenceNumber', namespaces=NAMESPACE)[0].text
        skip = False

        if self.collection == 'soviet-tv':
            container, folder = arn[16:].split('-')
            arn = "HU OSA 300-81-9:%s/%s" % (container, folder)

        if self.collection == 'samizdat-audio':
            title = xml.xpath('//osa:primaryTitle/osa:title', namespaces=NAMESPACE)[0].text
            date_from = xml.xpath('//osa:dateOfCreationNormalizedStart', namespaces=NAMESPACE)[0].text
            date_from = date_from[0:10]

            container, folder = arn[16:].split('/')
            container = int(container) - 159

            au = ArchivalUnit.objects.get(
                fonds='300', subfonds='85', series='54'
            )
            c, created = Container.objects.get_or_create(
                archival_unit=au,
                container_no=container,
                carrier_type=CarrierType.objects.get(type='Digital container')
            )
            fa_entity, created = FindingAidsEntity.objects.get_or_create(
                archival_unit=c.archival_unit,
                container=c,
                folder_no=int(folder),
                title=title,
                date_from=date_from
            )
            fa_entity.primary_type = PrimaryType.objects.get(type='Audio')
            fa_entity.save()
            arn = fa_entity.archival_reference_code

        if self.collection == 'information-items':
            title = xml.xpath('//osa:primaryTitle/osa:title', namespaces=NAMESPACE)[0].text
            date_from = xml.xpath('//osa:dateOfCreationNormalizedStart', namespaces=NAMESPACE)[0].text
            date_from = date_from[0:10]

            try:
                fa_entity = FindingAidsEntity.objects.get(
                    title=title
                )
                skip = True
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                skip = False

            if not skip:
                try:
                    fa_entity = FindingAidsEntity.objects.get(
                        title=title,
                        date_from=date_from
                    )
                except ObjectDoesNotExist:
                    return None
                except MultipleObjectsReturned:
                    if pid in self.helper_csv.keys():
                        note = self.helper_csv[pid]
                        try:
                            fa_entity = FindingAidsEntity.objects.get(
                                title=title,
                                date_from=date_from,
                                note=note
                            )
                        except ObjectDoesNotExist:
                            return None
            
            arn = fa_entity.archival_reference_code
        return arn

    def read_helper_csv(self, collection):
        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', '%s_reference_numbers.csv' % collection)

        with open(csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if collection == 'information-items':
                    legacy_id = row['legacy_id']
                    index = row['legacy_id'].rfind('-')
                    value = "%s/%s" % (row['legacy_id'][index+1:], legacy_id[index-2:index])
                    self.helper_csv[row['fedora_id']] = value
                else:
                    self.helper_csv[row['fedora_id']] = row['legacy_id']

    def write_csv(self, collection):
        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', '%s_datasheet.csv' % collection)

        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['fedora_id', 'reference_code', 'primary_type', 'access_copy', 'makedir', 'download_command',
                          'thumbnail_command', 'access_copy_command']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            sorted_data = sorted(self.csv, key=lambda x: x["access_copy"])

            for row in sorted_data:
                writer.writerow(row)

    def get_download_command(self, pid, did, main_directory, type):
        command = ''

        dir1 = pid[4:6]
        dir2 = pid[6:8]
        filename = pid.replace("osa:", "")

        if type == 'Textual':
            filetype = 'pdf'
            command = "cp /data/www/storage.osaarchivum.org/low/%s/%s/%s_l.%s ./textual/%s/%s.pdf" % (
                dir1, dir2, filename, filetype, main_directory, did
            )
        if type == 'Moving Image':
            filetype = 'mp4'
            command = "cp /data/www/storage.osaarchivum.org/low/%s/%s/%s_l.%s ./video/%s/%s/%s.mp4" % (
                dir1, dir2, filename, filetype, main_directory, did, did
            )
        if type == 'Audio':
            filetype = 'mp3'
            command = "cp /data/www/storage.osaarchivum.org/low/%s/%s/%s_l.%s ./audio/%s/%s.mp3" % (
                dir1, dir2, filename, filetype, main_directory, did
            )

        return command

    def get_thumbnail_command(self, pid, did, main_directory, type):
        command = ''

        dir1 = pid[4:6]
        dir2 = pid[6:8]
        filename = pid.replace("osa:", "")

        if type == 'Textual':
            command = 'convert -geometry x600 -quality 90 "%s.pdf[0]" "%s.jpg" ' % (did, did)
        if type == 'Audio':
            command = "cp /data/www/storage.osaarchivum.org/thumbnail/%s/%s/%s_t_001.jpg ./audio/%s/%s.jpg" % (
                dir1, dir2, filename, main_directory, did
            )
        if type == 'Moving Image':
            command = "cp /data/www/storage.osaarchivum.org/thumbnail/%s/%s/%s_t_001.jpg ./video/%s/%s/%s.jpg" % (
                dir1, dir2, filename, main_directory, did, did
            )

        return command

    def get_access_copy_command(self, pid, did, main_directory, type):
        command = ''

        dir1 = pid[4:6]
        dir2 = pid[6:8]
        filename = pid.replace("osa:", "")

        if type == 'Moving Image':
            command = "ffmpeg -i ./video/%s/%s/%s.mp4 -codec: copy -start_number 0 -hls_time 10 -hls_list_size 0 -bsf:v h264_mp4toannexb -f hls ./video/%s/%s/%s.m3u8" % (
                main_directory, did, did, main_directory, did, did
            )

        return command