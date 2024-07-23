import time

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity
from markdownify import markdownify as md


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fonds', dest='fonds', help='Fonds Number')
        parser.add_argument('--subfonds', dest='subfonds', help='Subfonds Number')
        parser.add_argument('--series', dest='series', help='Series Number')
        parser.add_argument('--all', dest='all', help='Index everything.')

    def handle(self, *args, **options):
        if options['all']:
            archival_units = ArchivalUnit.objects.filter()
            for archival_unit in archival_units.iterator():
                for fa in FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False).iterator():
                    self.convert_to_markdown(fa)

        else:
            archival_unit = ArchivalUnit.objects.get(fonds=options['fonds'],
                                                     subfonds=options['subfonds'],
                                                     series=options['series'])
            finding_aids_entities = FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False)
            for fa in finding_aids_entities.iterator():
                self.convert_to_markdown(fa)
    def convert_to_markdown(self, fa_entity):
        self.convert_field(fa_entity, 'contents_summary')
        self.convert_field(fa_entity, 'contents_summary_original')
        self.convert_field(fa_entity, 'physical_condition')
        self.convert_field(fa_entity, 'physical_description')
        self.convert_field(fa_entity, 'physical_description_original')
        self.convert_field(fa_entity, 'language_statement')
        self.convert_field(fa_entity, 'language_statement_original')
        self.convert_field(fa_entity, 'note')
        self.convert_field(fa_entity, 'note_original')
        self.convert_field(fa_entity, 'internal_note')
        fa_entity.save()

    def convert_field(self, fa_entity, field):
        if getattr(fa_entity, field):
            setattr(fa_entity, field, md(getattr(fa_entity, field), bullets='-'))

