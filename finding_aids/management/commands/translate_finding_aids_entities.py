import deepl
from django.conf import settings

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fonds', dest='fonds', help='Fonds Number')
        parser.add_argument('--subfonds', dest='subfonds', help='Subfonds Number')
        parser.add_argument('--series', dest='series', help='Series Number')
        parser.add_argument('--field_from', dest='field_from', help='Field to translate from.')
        parser.add_argument('--field_to', dest='field_to', help='Field to translate to.')
        parser.add_argument('--from_container', dest='from_container', help='Container to translate from.')
        parser.add_argument('--language_from', dest='language_from', help='Language to translate from.')
        parser.add_argument('--language_to', dest='language_to', help='Language to translate to.')

    def handle(self, *args, **options):
        archival_unit = ArchivalUnit.objects.get(fonds=options['fonds'],
                                                 subfonds=options['subfonds'],
                                                 series=options['series'])

        auth_key = getattr(settings, 'DEEPL_AUTH_KEY', None)
        translator = deepl.Translator(auth_key)

        finding_aids_entities = FindingAidsEntity.objects.filter(
            archival_unit=archival_unit,
            is_template=False,
            container__container_no__gte=options['from_container']
        )

        for fa_entity in finding_aids_entities:
            source_text = getattr(fa_entity, options['field_from'])
            if source_text:
                result = translator.translate_text(
                    text=source_text,
                    source_lang=options['language_from'],
                    target_lang=options['language_to'],
                )
                setattr(fa_entity, options['field_to'], result.text)
                print("%s -> %s" % (source_text, getattr(fa_entity, options['field_to'])))
                fa_entity.save()
