import os
import json

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fonds', dest='fonds', help='Fonds Number')
        parser.add_argument('--subfonds', dest='subfonds', help='Subfonds Number')
        # parser.add_argument('--series', dest='series', help='Series Number')

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)

        self.archival_unit = None

        self.fonds_data = {}
        self.subfonds_data = {}
        self.series_data = {}
        self.folders_items = []

    def handle(self, *args, **options):
        archival_units = ArchivalUnit.objects.filter(fonds=options['fonds'], subfonds=options['subfonds'], level='S').order_by('sort')

        for archival_unit in archival_units:
            if Isad.objects.filter(archival_unit=archival_unit).exists():
                self.archival_unit = archival_unit

                self.assemble_archival_unit_data('F')
                self.assemble_archival_unit_data('SF')
                self.assemble_archival_unit_data('S')

                self.assemble_finding_aids()

                output = {
                    'fonds': self.fonds_data,
                    'subfonds': self.subfonds_data,
                    'series': self.series_data,
                    'finding_aids': self.folders_items
                }

                filename = f"HU OSA {self.archival_unit.fonds}-{self.archival_unit.subfonds}-{self.archival_unit.series}_discuss_data.json"

                json_file = os.path.join(
                    os.getcwd(), 'finding_aids', 'management', 'commands', 'json', filename)

                with open(json_file, 'w') as f:
                    json.dump(output, f, indent=4)

                print (f"Exported data: {filename}")

    def assemble_archival_unit_data(self, level):
        if level == 'F':
            au = self.archival_unit.get_fonds()
        elif level == 'SF':
            au = self.archival_unit.get_subfonds()
        else:
            au = self.archival_unit

        data = {
            'orig_uuid': str(au.uuid),
            'dataset_type': 'COL',
            'title_en': au.title,
            'orig_uri': f"https://catalog.archivum.org/catalog/{au.isad.catalog_id}",
            'description': "",
            'start_date': au.isad.year_from,
            'end_date': au.isad.year_to,
            'archival_id': au.reference_code,
            'created_at': au.isad.date_created.isoformat(),
            'updated_at': au.isad.date_updated.isoformat() if au.isad.date_updated else au.isad.date_created.isoformat(),
            'data_source': 'Blinken OSA Archivum'
        }

        # Add description
        if au.isad.scope_and_content_abstract:
            if data['description'] != "":
                data['description'] += "\n\n"
            data['description'] += au.isad.scope_and_content_abstract
        if au.isad.scope_and_content_narrative:
            if data['description'] != "":
                data['description'] += "\n\n"
            data['description'] += "\n\n" + au.isad.scope_and_content_narrative

        # Amount
        fa_entity_count = FindingAidsEntity.objects.filter(archival_unit=au, is_template=False).count()
        data['amount'] = f"{fa_entity_count} Folder/Item records"

        # Add original title
        if au.title_original:
            data['title'] = au.title_original

        # Add notes
        notes = []

        # Note - Archival History
        if au.isad.archival_history:
            notes.append({
                'note_type': {'name': 'Archival History'},
                'text': au.isad.archival_history
            })

        # Note - Administrative History
        if au.isad.administrative_history:
            notes.append({
                'note_type': {'name': 'Administrative History'},
                'text': au.isad.administrative_history
            })

        # Note - Access Rights
        if level == 'S':
            notes.append({
                'note_type': {'name': 'Access Rights'},
                'text': self.get_access_rights(au.isad)
            })

        # Note - Reproduction Rights
        if au.isad.reproduction_rights and level == 'S':
            notes.append({
                'note_type': {'name': 'Reproduction Rights'},
                'text': au.isad.reproduction_rights.statement
            })

        # Note - System of arrangement information
        if au.isad.system_of_arrangement_information:
            notes.append({
                'note_type': {'name': 'System of Arrangement Information'},
                'text': au.isad.system_of_arrangement_information
            })

        # Note - Publication Note
        if au.isad.publication_note:
            notes.append({
                'note_type': {'name': 'Publication Note'},
                'text': au.isad.publication_note
            })

        # Note - System of arrangement information
        if au.isad.archivists_note:
            notes.append({
                'note_type': {'name': 'Archivists Note'},
                'text': au.isad.archivists_note
            })

        data['notes'] = notes

        if level == 'F':
            self.fonds_data = data
        elif level == 'SF':
            self.subfonds_data = data
        else:
            self.series_data = data

    def assemble_finding_aids(self):
        containers = Container.objects.filter(archival_unit=self.archival_unit).order_by('container_no')
        for container in containers.all():
            fa_entities = FindingAidsEntity.objects.filter(container=container).order_by('folder_no', 'sequence_no')
            for fa_entity in fa_entities.all():
                data = {
                    'orig_uuid': str(fa_entity.uuid),
                    'dataset_type': 'DOC',
                    'title_en': fa_entity.title,
                    'description': fa_entity.contents_summary,
                    'orig_uri': f"https://catalog.archivum.org/catalog/{fa_entity.catalog_id}",
                    'start_date': str(fa_entity.date_from),
                    'end_date': str(fa_entity.date_to),
                    'archival_id': fa_entity.archival_reference_code,
                    'created_at': fa_entity.date_created.isoformat(),
                    'updated_at': fa_entity.date_updated.isoformat() if fa_entity.date_updated else None,
                    'data_source': 'Blinken OSA Archivum'
                }

                notes = []
                # Note - Physical description
                if fa_entity.physical_description:
                    notes.append({
                        'note_type': {'name': 'Physical Description'},
                        'text': fa_entity.physical_description
                    })

                # Note - Physical condition
                if fa_entity.physical_condition:
                    notes.append({
                        'note_type': {'name': 'Physical Condition'},
                        'text': fa_entity.physical_condition
                    })

                # Note - Note information
                if fa_entity.note:
                    notes.append({
                        'note_type': {'name': 'Note'},
                        'text': fa_entity.note
                    })
                data['notes'] = notes

                people = []
                for person in fa_entity.subject_person.all():
                    people.append(self.create_person_record(person))

                for corporation in fa_entity.subject_corporation.all():
                    people.append(self.create_corporation_record(corporation))

                for person in fa_entity.findingaidsentityassociatedperson_set.all():
                    people.append(self.create_person_record(person.associated_person))

                for corporation in fa_entity.findingaidsentityassociatedcorporation_set.all():
                    people.append(self.create_corporation_record(corporation.associated_corporation))
                data['people'] = people

                self.folders_items.append(data)

    def create_person_record(self, person):
        data = {
            'uuid': f'osa:person_{person.id:05}',
            'person_type': 'PER',
            'first_name': person.first_name,
            'last_name': person.last_name,
            'wikidata': person.wikidata_id,
            'viaf': person.authority_url,
            'created_at': person.date_created.isoformat(),
            'updated_at': person.date_updated.isoformat(),
            'person_names': [],
            'data_source': 'Blinken OSA Archivum'
        }

        for pof in person.personotherformat_set.all():
            person_name = {
                'first_name': pof.first_name,
                'last_name': pof.last_name,
                'language': pof.language.iso_639_2 if pof.language else None
            }
            data['person_names'].append(person_name)
        return data

    def create_corporation_record(self, corporation):
        data = {
            'uuid': f'osa:corporation_{corporation.id:05}',
            'person_type': 'INS',
            'first_name': corporation.name,
            'wikidata': corporation.wikidata_id,
            'viaf': corporation.authority_url,
            'created_at': corporation.date_created.isoformat(),
            'updated_at': corporation.date_updated.isoformat(),
            'person_names': [],
            'data_source': 'Blinken OSA Archivum'
        }

        for cof in corporation.corporationotherformat_set.all():
            person_name = {
                'first_name': cof.name,
                'language': cof.language.iso_639_2 if cof.language else None
            }
            data['person_names'].append(person_name)
        return data

    def get_access_rights(self, obj):
        fa_entity_count = 0
        restricted_count = 0

        if obj.description_level == 'F':
            fa_entity_count = FindingAidsEntity.objects.filter(
                archival_unit__parent__parent=obj.archival_unit, is_template=False).count()
            restricted_count = FindingAidsEntity.objects.filter(
                archival_unit__parent__parent=obj.archival_unit, access_rights__id=3).count()

        if obj.description_level == 'SF':
            fa_entity_count = FindingAidsEntity.objects.filter(
                archival_unit__parent=obj.archival_unit, is_template=False).count()
            restricted_count = FindingAidsEntity.objects.filter(
                archival_unit__parent=obj.archival_unit, access_rights__id=3).count()

        if obj.description_level == 'S':
            fa_entity_count = FindingAidsEntity.objects.filter(
                archival_unit=obj.archival_unit, is_template=False).count()
            restricted_count = FindingAidsEntity.objects.filter(
                archival_unit=obj.archival_unit, access_rights__id=3).count()

        if fa_entity_count == restricted_count:
            return 'Restricted'

        if restricted_count == 0:
            return 'Not Restricted'

        return 'Partially Restricted (%s Folder/Item Restricted - %s Folder/Item Not Restricted)' % (
            restricted_count, (fa_entity_count - restricted_count)
        )