from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit


class Command(BaseCommand):
    def handle(self, *args, **options):
        export_data = []

        archival_units = ArchivalUnit.objects.filter(level="series")
        for archival_unit in archival_units.iterator():
            data = {"fonds": (archival_unit.get_fonds().title_full,)}

            if archival_unit.subfond != 0:
                sf = archival_units.get_subfonds()
                data["subfonds"] = f"{sf.reference_code} {sf.title}"

            data["series"] = f"{archival_unit.reference_code} {archival_unit.title}"

            export_data.append(data)
