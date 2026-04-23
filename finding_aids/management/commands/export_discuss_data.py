import os
import json

from django.core.management import BaseCommand
from django.db.models import Count, Q, Prefetch

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAssociatedPerson, \
    FindingAidsEntityAssociatedCorporation


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
        archival_units = ArchivalUnit.objects.filter(
            fonds=options['fonds'],
            subfonds=options['subfonds'],
            level='S'
        ).annotate(
            fa_non_template_count=Count('findingaidsentity', filter=Q(findingaidsentity__is_template=False), distinct=True)
        ).select_related(
            'isad',
            'parent',
            'parent__isad',
            'parent__parent',
            'parent__parent__isad'
        ).order_by('sort')

        for archival_unit in archival_units:
            if getattr(archival_unit, 'isad', None):
                if archival_unit.fa_non_template_count > 0:
                    self.archival_unit = archival_unit
                    self.folders_items = []

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
        fa_entities = FindingAidsEntity.objects.filter(
            archival_unit=self.archival_unit,
            is_template=False
        ).select_related(
            'container'
        ).prefetch_related(
            Prefetch('subject_person', to_attr='prefetched_subject_person'),
            Prefetch('subject_corporation', to_attr='prefetched_subject_corporation'),
            Prefetch(
                'findingaidsentityassociatedperson_set',
                queryset=FindingAidsEntityAssociatedPerson.objects.select_related('associated_person'),
                to_attr='prefetched_associated_people'
            ),
            Prefetch(
                'findingaidsentityassociatedcorporation_set',
                queryset=FindingAidsEntityAssociatedCorporation.objects.select_related('associated_corporation'),
                to_attr='prefetched_associated_corporations'
            )
        ).order_by('container__container_no', 'folder_no', 'sequence_no')

        people_ids = set()
        corporation_ids = set()
        for fa_entity in fa_entities:
            for person in getattr(fa_entity, 'prefetched_subject_person', []):
                people_ids.add(person.id)
            for corporation in getattr(fa_entity, 'prefetched_subject_corporation', []):
                corporation_ids.add(corporation.id)
            for associated in getattr(fa_entity, 'prefetched_associated_people', []):
                if associated.associated_person_id:
                    people_ids.add(associated.associated_person_id)
            for associated in getattr(fa_entity, 'prefetched_associated_corporations', []):
                if associated.associated_corporation_id:
                    corporation_ids.add(associated.associated_corporation_id)

        from authority.models import Person, Corporation
        people_map = {
            p.id: p for p in Person.objects.filter(id__in=people_ids).prefetch_related('personotherformat_set__language')
        }
        corporations_map = {
            c.id: c for c in Corporation.objects.filter(id__in=corporation_ids).prefetch_related(
                'corporationotherformat_set__language'
            )
        }

        for fa_entity in fa_entities:
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
            if fa_entity.physical_description:
                notes.append({
                    'note_type': {'name': 'Physical Description'},
                    'text': fa_entity.physical_description
                })
            if fa_entity.physical_condition:
                notes.append({
                    'note_type': {'name': 'Physical Condition'},
                    'text': fa_entity.physical_condition
                })
            if fa_entity.note:
                notes.append({
                    'note_type': {'name': 'Note'},
                    'text': fa_entity.note
                })
            data['notes'] = notes

            people = []
            for person in getattr(fa_entity, 'prefetched_subject_person', []):
                cached_person = people_map.get(person.id)
                if cached_person:
                    people.append(self.create_person_record(cached_person))

            for corporation in getattr(fa_entity, 'prefetched_subject_corporation', []):
                cached_corporation = corporations_map.get(corporation.id)
                if cached_corporation:
                    people.append(self.create_corporation_record(cached_corporation))

            for associated in getattr(fa_entity, 'prefetched_associated_people', []):
                cached_person = people_map.get(associated.associated_person_id)
                if cached_person:
                    people.append(self.create_person_record(cached_person))

            for associated in getattr(fa_entity, 'prefetched_associated_corporations', []):
                cached_corporation = corporations_map.get(associated.associated_corporation_id)
                if cached_corporation:
                    people.append(self.create_corporation_record(cached_corporation))

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
        base_filter = Q(is_template=False)
        if obj.description_level == 'F':
            base_filter &= Q(archival_unit__parent__parent=obj.archival_unit)
        elif obj.description_level == 'SF':
            base_filter &= Q(archival_unit__parent=obj.archival_unit)
        else:
            base_filter &= Q(archival_unit=obj.archival_unit)

        counts = FindingAidsEntity.objects.filter(base_filter).aggregate(
            fa_entity_count=Count('id'),
            restricted_count=Count('id', filter=Q(access_rights__id=3))
        )
        fa_entity_count = counts['fa_entity_count'] or 0
        restricted_count = counts['restricted_count'] or 0

        if fa_entity_count == restricted_count:
            return 'Restricted'

        if restricted_count == 0:
            return 'Not Restricted'

        return 'Partially Restricted (%s Folder/Item Restricted - %s Folder/Item Not Restricted)' % (
            restricted_count, (fa_entity_count - restricted_count)
        )
