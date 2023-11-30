import csv
import os
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand, CommandError
from lxml import etree

from archival_unit.models import ArchivalUnit
from authority.models import Language, Genre, Person, PersonOtherFormat, Corporation, Place, Country
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType, AccessRight, ExtentUnit, PersonRole, CorporationRole, \
    Keyword
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity, FindingAidsEntityLanguage, FindingAidsEntityCreator, \
    FindingAidsEntityExtent, FindingAidsEntityAssociatedPerson, FindingAidsEntityAssociatedCorporation, \
    FindingAidsEntityAssociatedPlace, FindingAidsEntityAssociatedCountry

FEDORA_URL = getattr(settings, "FEDORA_URL")
FEDORA_RISEARCH = '%s/risearch' % FEDORA_URL
FEDORA_ADMIN = getattr(settings, "FEDORA_ADMIN")
FEDORA_ADMIN_PASS = getattr(settings, "FEDORA_ADMIN_PASS")

NSP = {'osa': 'http://greenfield.osaarchivum.org/ns/item'}

unicode = str


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.pid = None
        self.xml = None
        self.level = 'L1'
        self.carrier_type = None
        self.archival_unit = None
        self.current_container = None
        self.fa_entity = None

    def add_arguments(self, parser):
        parser.add_argument('collection', help='Collection identifier')
        parser.add_argument('level', help='Collection identifier')
        parser.add_argument('container_type', help='Collection identifier')

    def handle(self, *args, **options):
        collection = options.get('collection')
        self.level = options.get('level')

        carrier_type = options.get('container_type')
        try:
            self.carrier_type = CarrierType.objects.get(type=carrier_type)
        except ObjectDoesNotExist:
            raise CommandError("Wrong carrier type: %s" % carrier_type)

        csv_file = os.path.join(
            os.getcwd(), 'digitization', 'management', 'commands', 'csv', '%s_reference_numbers.csv' % collection)

        with open(csv_file, newline='', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.pid = row['fedora_id']
                did = row['did']

                self.get_document()
                self.create_finding_aids_entity(did)
                self.create_digital_version(did)
                pass

    def get_document(self):
        r = requests.get("%s/objects/%s/datastreams/ITEM-ARC-EN/content" % (FEDORA_URL, self.pid))
        if r.ok:
            self.xml = r.text

    def create_finding_aids_entity(self, did):
        if self.level == 'L1':
            (hu, osa, fonds, subfonds, series, container_no, folder_no) = did.split('_')
            sequence_no = 0
        else:
            (hu, osa, fonds, subfonds, series, container_no, folder_no, sequence_no) = did.split('_')

        fonds = int(fonds)
        subfonds = int(subfonds)
        series = int(series)
        container_no = int(container_no)
        folder_no = int(folder_no)
        sequence_no = int(sequence_no)

        archival_unit = ArchivalUnit.objects.get(fonds=fonds, subfonds=subfonds, series=series)
        container, created = Container.objects.get_or_create(
            archival_unit=archival_unit,
            carrier_type=self.carrier_type,
            container_no=container_no
        )

        xml = etree.fromstring(self.xml)
        title = xml.xpath('//osa:primaryTitle/osa:title', namespaces=NSP)[0].text
        title_given = xml.xpath('//osa:primaryTitle/osa:titleGiven', namespaces=NSP)[0].text == 'true'

        date_from = datetime.strptime(xml.xpath('//osa:dateOfCreationNormalizedStart', namespaces=NSP)[0].text,
                               '%Y-%m-%dT%H:%M:%SZ')

        try:
            fa_entity = FindingAidsEntity.objects.get(
                description_level=self.level,
                container=container,
                folder_no=folder_no,
                sequence_no=sequence_no
            )
        except ObjectDoesNotExist:
            fa_entity = FindingAidsEntity.objects.create(
                uuid=self.pid.replace('osa:', '').replace('-', ''),
                description_level=self.level,
                level='I',
                container=container,
                archival_unit=archival_unit,
                folder_no=folder_no,
                sequence_no=sequence_no,
                title=title,
                date_from=date_from
            )

        # Title
        fa_entity.uuid = self.pid.replace('osa:', '').replace('-', '')
        fa_entity.level = 'I'
        fa_entity.title = title
        fa_entity.title_given = title_given

        # Dates
        date_to = datetime.strptime(
            xml.xpath('//osa:dateOfCreationNormalizedEnd', namespaces=NSP)[0].text, '%Y-%m-%dT%H:%M:%SZ')
        if date_to:
            fa_entity.date_to = date_to

        fa_entity.date_ca_span = int(xml.xpath('//osa:dateOfCreationSpan', namespaces=NSP)[0].text)

        # Primary Type
        fa_entity.primary_type = self.get_primary_type(xml)

        # Contents Summary
        contents_summary = []
        for cs in xml.xpath('//osa:contentsSummary', namespaces=NSP):
            contents_summary.append('%s<br/>' % cs.text)
        if len(contents_summary) > 0:
            contents_summary = '<p>%s</p>' % ''.join(contents_summary)
        else:
            contents_summary = ''

        contents_table = []
        for ct in xml.xpath('//osa:contentsTable', namespaces=NSP):
            contents_table.append('<li>%s</li>' % ct.text)
        if len(contents_table) > 0:
            contents_table = '<ul>%s</ul>' % ''.join(contents_table)
        else:
            contents_table = ''
        fa_entity.contents_summary = contents_summary + contents_table

        # Access Rights
        fa_entity.access_rights = AccessRight.objects.get(statement='Not Restricted')

        # Administrative history
        administrative_history = []
        for ah in xml.xpath('//osa:administrativeHistory', namespaces=NSP):
            administrative_history.append(ah.text)
        fa_entity.administrative_history = ' '.join(administrative_history)

        # Physical condition
        elements = xml.xpath('//osa:physicalCondition', namespaces=NSP)
        if len(elements) > 0:
            fa_entity.physical_condition = elements[0].text

        # Physical description
        elements = xml.xpath('//osa:physicalDescription', namespaces=NSP)
        if len(elements) > 0:
            fa_entity.physical_description = elements[0].text

        # Language
        for language in xml.xpath('//osa:documentLanguage', namespaces=NSP):
            try:
                language = Language.objects.get(language=language.text)
                FindingAidsEntityLanguage.objects.get_or_create(
                    fa_entity=fa_entity,
                    language=language
                )
            except ObjectDoesNotExist:
                pass

        # Genre
        for genre in xml.xpath('//osa:genre', namespaces=NSP):
            genre, created = Genre.objects.get_or_create(genre=genre.text)
            fa_entity.genre.add(genre)

        # Creators
        fields = ['//osa:creatorPersonalFree', '//osa:creatorCorporateFree']
        for field in fields:
            for creator in xml.xpath(field, namespaces=NSP):
                name = creator.xpath('./osa:name', namespaces=NSP)[0].text
                role = creator.xpath('./osa:role', namespaces=NSP)[0].text
                if role == 'collector':
                    role = 'COL'
                else:
                    role = 'CRE'
                FindingAidsEntityCreator.objects.get_or_create(
                    fa_entity=fa_entity,
                    creator=name,
                    role=role
                )

        # Extent
        for extent in xml.xpath('//osa:subExtent', namespaces=NSP):
            number = extent.xpath('./osa:subExtentNumber', namespaces=NSP)[0].text
            unit = extent.xpath('./osa:subExtentUnit', namespaces=NSP)[0].text

            if unit == 'hh:mm:ss':
                hours, minutes, seconds = number.split(':')
                fa_entity.time_end = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
            else:
                if unit == 'page':
                    unit = ExtentUnit.objects.get(unit='pages')
                else:
                    unit, created = ExtentUnit.objects.get_or_create(
                        unit=unit
                    )

                FindingAidsEntityExtent.objects.get_or_create(
                    fa_entity=fa_entity,
                    extent_number=number,
                    extent_unit=unit
                )

        # Associated Person
        for associated_person in xml.xpath('//osa:associatedPersonal', namespaces=NSP):
            name = associated_person.xpath('./osa:name', namespaces=NSP)[0].text
            role = None
            alternative_names = associated_person.xpath('./osa:alternative_name', namespaces=NSP)

            if ',' in name:
                last_name, first_name = name.split(', ')
            else:
                first_name = name.strip()
                last_name = ''

            person, created = Person.objects.get_or_create(
                first_name=first_name.strip(),
                last_name=last_name.strip()
            )

            element = associated_person.xpath('./osa:role', namespaces=NSP)
            if len(element) > 0:
                r = element[0].text
                role, created = PersonRole.objects.get_or_create(
                    role=r.strip().capitalize()
                )

            for alternative_name in alternative_names:
                if ',' in alternative_name:
                    last_name, first_name = alternative_name.split(', ')
                else:
                    first_name = alternative_name.strip()
                    last_name = ''

                person, created = PersonOtherFormat.objects.get_or_create(
                    person=person,
                    first_name=first_name.strip(),
                    last_name=last_name.strip()
                )

            fa_ap, created = FindingAidsEntityAssociatedPerson.objects.get_or_create(
                fa_entity=fa_entity,
                associated_person=person,
            )

            if role:
                fa_ap.role = role
                fa_ap.save()

        # Associated Corporation
        for associated_corporation in xml.xpath('//osa:associatedCorporate', namespaces=NSP):
            name = associated_corporation.xpath('./osa:name', namespaces=NSP)[0].text
            role = None

            element = associated_corporation.xpath('./osa:role', namespaces=NSP)
            if len(element) > 0:
                r = element[0].text
                role, created = CorporationRole.objects.get_or_create(
                    role=r.strip().capitalize()
                )

            corporation, created = Corporation.objects.get_or_create(
                name=name.strip()
            )

            fa_ac, created = FindingAidsEntityAssociatedCorporation.objects.get_or_create(
                fa_entity=fa_entity,
                associated_corporation=corporation,
            )

            if role:
                fa_ac.role = role
                fa_ac.save()

        # Associated Place
        for ap in xml.xpath('//osa:associatedPlace/osa:place', namespaces=NSP):
            if ap.text.strip():
                place, created = Place.objects.get_or_create(
                    place=ap.text.strip()
                )

                FindingAidsEntityAssociatedPlace.objects.create(
                    fa_entity=fa_entity,
                    associated_place=place
                )

        # Associated Country
        for ac in xml.xpath('//osa:associatedCountry/osa:country', namespaces=NSP):
            if ac.text.strip():
                country, created = Country.objects.get_or_create(
                    country=ac.text.strip()
                )

                FindingAidsEntityAssociatedCountry.objects.create(
                    fa_entity=fa_entity,
                    associated_country=country
                )

        # Spatial Coverage Place
        for scp in xml.xpath('//osa:spatialCoverage/osa:coverage', namespaces=NSP):
            if scp.text.strip():
                if scp.text.strip().find('('):
                    pl = scp.text.strip()[:scp.text.strip().find('(')-1]
                else:
                    pl = scp.text.strip()
                place, created = Place.objects.get_or_create(
                    place=pl.strip()
                )
                fa_entity.spatial_coverage_place.add(place)

        # Spatial Coverage Country
        for sc in xml.xpath('//osa:spatialCoverageCountry/osa:country', namespaces=NSP):
            if sc.text.strip():
                country, created = Country.objects.get_or_create(
                    country=sc.text.strip()
                )
                fa_entity.spatial_coverage_country.add(country)

        # Subject People
        fields = ['//osa:subjectPersonal/osa:name', '//osa:subjectPersonalFree']
        for field in fields:
            for name in xml.xpath(field, namespaces=NSP):
                if name.text.strip():
                    if ',' in name:
                        last_name, first_name = name.split(', ')
                    else:
                        first_name = name.text.strip()
                        last_name = ''
                    person, created = Person.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name
                    )
                    fa_entity.subject_person.add(person)

        # Subject People
        fields = ['//osa:subjectCorporate/osa:name', '//osa:subjectCorporateFree']
        for field in fields:
            for name in xml.xpath(field, namespaces=NSP):
                if name.text.strip():
                    corporation, created = Corporation.objects.get_or_create(
                        name=name,
                    )
                    fa_entity.subject_corporation.add(corporation)

        # Subject Keyword
        for keyword in xml.xpath('//osa:subjectFree', namespaces=NSP):
            if keyword.text.strip():
                keyword, created = Keyword.objects.get_or_create(
                    keyword=keyword.text.strip()
                )
                fa_entity.subject_keyword.add(keyword)

        # Notes
        elements = xml.xpath('//osa:note', namespaces=NSP)
        if len(elements) > 0:
            fa_entity.note = elements[0].text

        fa_entity.published = True

        try:
            fa_entity.save()
        except Exception:
            pass

        self.fa_entity = fa_entity
        print("Added record %s" % fa_entity.archival_reference_code)

    def get_primary_type(self, xml):
        ptype = xml.xpath('//osa:primaryType', namespaces=NSP)[0].text
        if ptype == "Text" or ptype == 'Textual' or ptype == 'text' or ptype == 'textual':
            return PrimaryType.objects.get(type="Textual")
        if ptype == "Moving Image" or ptype == 'moving image':
            return PrimaryType.objects.get(type="Moving Image")
        if ptype == "Still Image" or ptype == 'still image':
            return PrimaryType.objects.get(type="Still Image")
        if ptype == "sound":
            return PrimaryType.objects.get(type="Audio")
        return None

    def create_digital_version(self, did):
        access_copy, created = DigitalVersion.objects.get_or_create(
            finding_aids_entity=self.fa_entity,
            identifier=did,
            level='A',
            filename="%s.pdf" % did,
            available_online=True
        )
        access_copy.finding_aids_entity.save()
