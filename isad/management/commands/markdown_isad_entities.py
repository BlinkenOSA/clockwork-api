import time

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity
from markdownify import markdownify as md

from isad.models import Isad


class Command(BaseCommand):
    def handle(self, *args, **options):
        isad_records = Isad.objects.all()
        for isad_record in isad_records.iterator():
            self.convert_to_markdown(isad_record)

    def convert_to_markdown(self, isad):
        # self.convert_field(isad, 'administrative_history')
        # self.convert_field(isad, 'administrative_history_original')
        # self.convert_field(isad, 'archival_history')
        # self.convert_field(isad, 'archival_history_original')
        # self.convert_field(isad, 'scope_and_content_abstract')
        # self.convert_field(isad, 'scope_and_content_abstract_original')
        # self.convert_field(isad, 'appraisal')
        # self.convert_field(isad, 'appraisal_original')
        # self.convert_field(isad, 'system_of_arrangement_information')
        # self.convert_field(isad, 'system_of_arrangement_information_original')
        # self.convert_field(isad, 'physical_characteristics')
        # self.convert_field(isad, 'physical_characteristics_original')

        self.convert_field(isad, 'scope_and_content_narrative')
        self.convert_field(isad, 'scope_and_content_narrative_original')

        try:
            isad.save()
            print("Markdown created for: %s" % isad.reference_code)
        except Exception:
            print("There was a problem saving ISAD(G) entity: %s" % isad.reference_code)

    def convert_field(self, isad, field):
        if getattr(isad, field):
            setattr(isad, field, md(getattr(isad, field), bullets='-'))

