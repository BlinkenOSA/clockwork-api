import time

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity

from deep_translator import GoogleTranslator


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fonds', dest='fonds', help='Fonds Number')
        parser.add_argument('--subfonds', dest='subfonds', help='Subfonds Number')
        parser.add_argument('--series', dest='series', help='Series Number')
        parser.add_argument('--field_from', dest='field_from', help='Field to translate from.')
        parser.add_argument('--field_to', dest='field_to', help='Field to translate to.')
        parser.add_argument('--language_from', dest='language_from', help='Language to translate from.')
        parser.add_argument('--language_to', dest='language_to', help='Language to translate to.')

    def handle(self, *args, **options):
        archival_unit = ArchivalUnit.objects.get(fonds=options['fonds'],
                                                 subfonds=options['subfonds'],
                                                 series=options['series'])

        finding_aids_entities = FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False)
        for fa_entity in finding_aids_entities:
            translator = GoogleTranslator(source=options['language_from'], target=options['language_to'])
            if getattr(fa_entity, options['field_from']):
                if len(getattr(fa_entity, options['field_from'])) < 5000:
                    setattr(fa_entity, options['field_to'], translator.translate(getattr(fa_entity, options['field_from'])))
                    print("%s -> %s" % (getattr(fa_entity, options['field_from']), getattr(fa_entity, options['field_to'])))
                    fa_entity.save()
                    time.sleep(0.5)