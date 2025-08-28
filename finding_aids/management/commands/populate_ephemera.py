import datetime
import re
import urllib
from io import BytesIO, StringIO

import unicodedata

import pymarc as pymarc
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from authority.models import Genre, Person, Corporation, Country, Place
from container.models import Container
from controlled_list.models import CarrierType, AccessRight, Locale, PersonRole, PrimaryType, Keyword, CorporationRole
from digitization.models import DigitalVersion
from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator
from finding_aids.models import FindingAidsEntity, FindingAidsEntityCreator, FindingAidsEntityAssociatedPerson, \
    FindingAidsEntityAssociatedCorporation

FEDORA_URL = getattr(settings, "FEDORA_URL")
FEDORA_RISEARCH = '%s/risearch' % FEDORA_URL
FEDORA_ADMIN = getattr(settings, "FEDORA_ADMIN")
FEDORA_ADMIN_PASS = getattr(settings, "FEDORA_ADMIN_PASS")

NSP = {'osa': 'http://greenfield.osaarchivum.org/ns/item'}

unicode = str

RI_QUERY = "select $pid $state $title \
            from    <#ri> \
            where   $object <fedora-model:state> $state \
            and     ($object <fedora-model:hasModel> <info:fedora/osa:cm-item-arc> \
            or      $object <fedora-model:hasModel> <info:fedora/osa:cm-item-lib>) \
            and     $object <dc:identifier> $pid \
            and     $object <dc:title> $title \
            and     $object <fedora-view:lastModifiedDate> $date \
            and     $object <info:fedora/fedora-system:def/relations-external#isMemberOfCollection> %s \
            order by $title"

collection_id = '<info:fedora/osa:554e8ec5-a131-4087-9b5d-4551cc82b291>'


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.current_pid = None
        self.container_no = 0
        self.folder_no = 0
        self.sequence_no = 0
        self.pids = []
        self.xml = None
        self.xml_hu = None
        self.level = 'L2'
        self.archival_unit = ArchivalUnit.objects.get(fonds=300, subfonds=55, series=7)
        self.locale = 'PL'
        self.current_container = None
        self.fa_entity = None

    def handle(self, *args, **options):
        self.get_pidlist(collection_id)
        for idx, pid in enumerate(self.pids):
            self.current_pid = pid

            # Get Documents
            self.get_document()

            # Get Numbers
            self.get_numbers()

            # Get Container
            self.get_container()

            # Create FA record
            self.create_finding_aids_entity()

    def get_pidlist(self, collection):
        ri_query = RI_QUERY % collection
        query = FEDORA_RISEARCH + '?type=tuples&lang=itql&format=json&query=' + urllib.parse.quote_plus(ri_query)

        r = requests.get(query)
        if r.ok:
            response = r.json()
            self.pids = list(map(lambda x: x['pid'], response['results']))

    def get_document(self):
        r = requests.get("%s/objects/%s/datastreams/ITEM-LIB-EN/content" % (FEDORA_URL, self.current_pid))
        r.encoding = 'UTF-8'
        if r.ok:
            self.xml = r.text

        if self.locale != 'EN':
            r = requests.get("%s/objects/%s/datastreams/ITEM-LIB-%s/content" % (FEDORA_URL, self.current_pid, self.locale))
            r.encoding = 'UTF-8'
            if r.ok:
                self.xml_hu = r.text

    def get_numbers(self):
        xml_file = StringIO(self.xml)
        marc = pymarc.marcxml.parse_xml_to_array(xml_file)[0]
        arn = marc['099']['f']
        self.container_no, self.folder_no, self.sequence_no = arn.split('-')

    def get_container(self):
        self.current_container, created = Container.objects.get_or_create(
            archival_unit=self.archival_unit,
            container_no=int(self.container_no)
        )

    def create_finding_aids_entity(self):
        xml_file = StringIO(self.xml)
        xml_file_pl = StringIO(self.xml_hu)

        marc = pymarc.marcxml.parse_xml_to_array(xml_file)[0]
        marc_pl = pymarc.marcxml.parse_xml_to_array(xml_file_pl)[0]

        uuid = self.current_pid.replace("osa:", "").replace('-', "")
        title = marc['242']['a']
        title_original = marc.title

        if int(self.container_no) == 2 and int(self.folder_no) == 5:
            self.sequence_no = int(self.sequence_no) - 10

        fa_entity, created = FindingAidsEntity.objects.get_or_create(
            uuid=uuid,
            container=self.current_container,
            archival_unit=self.archival_unit,
            folder_no=int(self.folder_no),
            sequence_no=int(self.sequence_no),
            original_locale=Locale.objects.get(id=self.locale),
            primary_type=PrimaryType.objects.get(type='Still Image'),
            description_level=self.level,
            level='I',
            title=title,
            title_original=title_original,
        )

        if marc.pubyear:
            if marc.pubyear.find("[") != -1:
                pubyear = marc.pubyear.replace('[', '').replace('ca.', '').replace(']', '')
                fa_entity.date_from = '%s-00-00' % pubyear.strip()
                fa_entity.date_ca_span = 2
            else:
                fa_entity.date_from = '%s-00-00' % marc.pubyear

        access_rights = AccessRight.objects.get(statement='Not Restricted')
        fa_entity.access_rights = access_rights

        try:
            contents_summary = marc['520']['a']
            fa_entity.contents_summary = contents_summary
        except KeyError:
            pass

        try:
            contents_summary_hu = marc_pl['520']['a']
            fa_entity.contents_summary_original = contents_summary_hu
        except KeyError:
            pass

        # Form / Genre
        for f in marc.get_fields('655'):
            for subfield in f.get_subfields('a'):
                if subfield == 'Propaganda':
                    subfield = 'Propaganda films'
                genre, created = Genre.objects.get_or_create(genre=subfield)
                fa_entity.genre.add(genre)

        # Physical Description
        fa_entity.physical_description = ' '.join(marc.physicaldescription[0].get_subfields('a', 'b', 'c'))
        fa_entity.physical_description_original = ' '.join(marc_pl.physicaldescription[0].get_subfields('a', 'b','c'))

        # Creator
        try:
            creator, created = FindingAidsEntityCreator.objects.get_or_create(
                fa_entity=fa_entity,
                creator=marc['110']['a']
            )
        except KeyError:
            pass

        # Subjects
            # People
            for f in marc.get_fields('600'):
                # Name
                name = f.get('a')

                if name:
                    name = re.sub('\u200f', '', name)

                    if name.endswith(","):
                        name = name[:-1]
                    try:
                        last_name, first_name = name.split(', ')
                    except ValueError:
                        parts = name.split(', ')
                        if len(parts) == 3:
                            last_name, first_name, middle_name = parts
                        else:
                            first_name = parts

                    person, created = Person.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name
                    )

                    # Subject Record
                    fa_entity.subject_person.add(person)

            # Corporations
            for f in marc.get_fields('610'):
                # Name
                name = f.get('a')
                corporation, created = Corporation.objects.get_or_create(
                    name=name,
                )

                # Subject Record
                fa_entity.subject_corporation.add(corporation)

        # Contributors
        for f in marc.get_fields('700'):
            # Name
            name = f.get('a')
            last_name, first_name = name.split(', ')
            person, created = Person.objects.get_or_create(
                first_name=first_name,
                last_name=last_name
            )

            # Role
            r = f.get('e')
            role, created = PersonRole.objects.get_or_create(
                role=r
            )

            # Contributor Record
            fa_ap, created = FindingAidsEntityAssociatedPerson.objects.get_or_create(
                fa_entity=fa_entity,
                associated_person=person,
                role=role
            )

        for f in marc.get_fields('710'):
            # Name
            name = f.get('a')
            corporation, created = Corporation.objects.get_or_create(
                name=name
            )

            # Role
            r = f.get('e')
            role, created = CorporationRole.objects.get_or_create(
                role=r
            )

            # Contributor Record
            fa_ac, created = FindingAidsEntityAssociatedCorporation.objects.get_or_create(
                fa_entity=fa_entity,
                associated_corporation=corporation,
                role=role
            )

        # Spatial coverage
        for f in marc.get_fields('651'):
            sf = f.get('a')
            try:
                country = Country.objects.get(country=sf)
                fa_entity.spatial_coverage_country.add(country)
            except ObjectDoesNotExist:
                place, created = Place.objects.get_or_create(
                    place=sf
                )
                fa_entity.spatial_coverage_place.add(place)

        # Keywords
        for f in marc.get_fields('653'):
            for value in f.get_subfields('a'):
                keyword, created = Keyword.objects.get_or_create(
                    keyword=value
                )
                fa_entity.subject_keyword.add(keyword)

        # Notes
        try:
            fa_entity.note = marc['500']['a']
        except KeyError:
            pass

        try:
            fa_entity.note_original = marc_pl['500']['a']
        except KeyError:
            pass

        fa_entity.digital_version_exists = True

        fa_entity.save()
        print("Data migrated to: %s" % fa_entity.archival_reference_code)

