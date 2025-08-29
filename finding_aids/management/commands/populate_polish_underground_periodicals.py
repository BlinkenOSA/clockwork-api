import csv
import os
from io import StringIO

import pymarc
import requests
from django.conf import settings
from django.core.management import BaseCommand
from setuptools.dist import sequence

from archival_unit.models import ArchivalUnit
from authority.models import Corporation, Person
from container.models import Container
from controlled_list.models import CarrierType, Locale, PrimaryType, AccessRight, PersonRole, CorporationRole
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAssociatedPerson, \
    FindingAidsEntityAssociatedCorporation

FEDORA_URL = getattr(settings, "FEDORA_URL")
FEDORA_RISEARCH = '%s/risearch' % FEDORA_URL
FEDORA_ADMIN = getattr(settings, "FEDORA_ADMIN")
FEDORA_ADMIN_PASS = getattr(settings, "FEDORA_ADMIN_PASS")

NSP = {'osa': 'http://greenfield.osaarchivum.org/ns/item'}

unicode = str


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.current_pid = None
        self.container_no = 0
        self.folder_no = 0
        self.sequence_no = 0
        self.pids = []
        self.xml = None
        self.xml_pl = None
        self.level = 'L1'
        self.archival_unit = ArchivalUnit.objects.get(fonds=444, subfonds=0, series=1)
        self.locale = 'PL'
        self.current_container = None
        self.fa_entity = None

    def handle(self, *args, **options):
        csv_file = os.path.join(
            os.getcwd(), 'finding_aids', 'management', 'commands', 'csv', 'polish_underground_periodicals.csv')

        with open(csv_file, newline='', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            series_name = None

            for row in reader:
                self.current_pid = row['uuid'].strip()

                if series_name != row['series'].strip():
                    self.container_no = self.container_no + 1
                    self.folder_no = 1
                    series_name = row['series'].strip()
                else:
                    self.folder_no = self.folder_no + 1

                # Get or create container
                self.current_container, created = Container.objects.get_or_create(
                    archival_unit=self.archival_unit,
                    container_no=self.container_no,
                    carrier_type=CarrierType.objects.get(type='Digital container')
                )

                # Download document
                self.get_document()

                # Create FA record
                self.create_finding_aids_entity()

                # Create Digital version
                self.create_digital_version()

    def get_document(self):
        r = requests.get("%s/objects/%s/datastreams/ITEM-LIB-EN/content" % (FEDORA_URL, self.current_pid))
        r.encoding = 'UTF-8'
        if r.ok:
            self.xml = r.text

        if self.locale != 'EN':
            r = requests.get("%s/objects/%s/datastreams/ITEM-LIB-%s/content" % (FEDORA_URL, self.current_pid, self.locale))
            r.encoding = 'UTF-8'
            if r.ok:
                self.xml_pl = r.text

    def create_finding_aids_entity(self):
        xml_file = StringIO(self.xml)
        xml_file_pl = StringIO(self.xml_pl)

        marc = pymarc.marcxml.parse_xml_to_array(xml_file)[0]
        marc_pl = pymarc.marcxml.parse_xml_to_array(xml_file_pl)[0]

        uuid = self.current_pid.replace("osa:", "").replace('-', "")
        title = marc.title

        fa_entity, created = FindingAidsEntity.objects.get_or_create(
            uuid=uuid,
            container=self.current_container,
            archival_unit=self.archival_unit,
            folder_no=int(self.folder_no),
            sequence_no=int(self.sequence_no),
            original_locale=Locale.objects.get(id=self.locale),
            primary_type=PrimaryType.objects.get(type='Textual'),
            description_level=self.level,
            level='I',
            title=title
        )

        fa_entity.title_original = marc_pl.title

        # Date From
        if marc.pubyear:
            if marc.pubyear.find("[") != -1:
                pubyear = marc.pubyear.replace('[', '').replace('ca.', '').replace(']', '')
                fa_entity.date_from = '%s-00-00' % pubyear.strip()
                fa_entity.date_ca_span = 2
            else:
                fa_entity.date_from = '%s-00-00' % marc.pubyear

        # Access Rights
        access_rights = AccessRight.objects.get(statement='Not Restricted')
        fa_entity.access_rights = access_rights

        # Contents Summary
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

        # Physical Description
        try:
            physical_description = marc['310']['a']
        except KeyError:
            pass
        fa_entity.physical_description = ' '.join(marc.physicaldescription[0].get_subfields('a', 'b', 'c'))
        fa_entity.physical_description += f"\n{physical_description}"

        try:
            physical_description = marc_pl['310']['a']
        except KeyError:
            pass
        fa_entity.physical_description_original = ' '.join(marc_pl.physicaldescription[0].get_subfields('a', 'b', 'c'))
        fa_entity.physical_description_original += f"\n{physical_description}"

        # Contributors
        for f in marc.get_fields('700'):
            # Name
            name = f.get('a')

            if name:
                try:
                    last_name, first_name = name.split(', ', 1)
                    skip = False
                except ValueError:
                    skip = True

                if not skip:
                    first_name = first_name.replace(",", "")
                    person, created = Person.objects.get_or_create(
                        first_name=first_name.strip(),
                        last_name=last_name.strip()
                    )

                    # Role
                    r = f.get('e')
                    if r:
                        role, created = PersonRole.objects.get_or_create(
                            role=r.strip()
                        )
                    else:
                        role = None

                    # Contributor Record
                    fa_ap, created = FindingAidsEntityAssociatedPerson.objects.get_or_create(
                        fa_entity=fa_entity,
                        associated_person=person,
                        role=role
                    )

        for f in marc.get_fields('710'):
            # Name
            name = f.get('a')
            if name:
                corporation, created = Corporation.objects.get_or_create(
                    name=name.strip()
                )

                # Role
                r = f.get('e')
                if r:
                    role, created = CorporationRole.objects.get_or_create(
                        role=r.strip()
                    )
                else:
                    role = None

                # Contributor Record
                fa_ac, created = FindingAidsEntityAssociatedCorporation.objects.get_or_create(
                    fa_entity=fa_entity,
                    associated_corporation=corporation,
                    role=role
                )

        fa_entity.save()

        identifier = "HU_OSA_444_0_1_%04d_%04d" % (fa_entity.container.container_no, fa_entity.folder_no)

        digital_version, created = DigitalVersion.objects.get_or_create(
            finding_aids_entity=fa_entity,
            identifier=identifier,
            level='A',
            digital_collection='Polish Underground Periodicals',
            filename=f"{identifier}.pdf",
            available_online=True
        )

        print(f"Processed: {fa_entity.archival_reference_code} - {fa_entity.title}")