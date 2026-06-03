import time

from django.core.management import BaseCommand
from django.db.models import Q

from clockwork_api.services.ark import ensure_ark
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class Command(BaseCommand):
    help = "Create missing ARKs for published ISAD and finding aids records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            choices=["all", "finding_aids", "isad"],
            default="all",
            help="Limit ARK creation to a single model type.",
        )
        parser.add_argument(
            "--ids",
            nargs="+",
            type=int,
            help="Optional list of primary keys to process.",
        )
        parser.add_argument(
            "--fonds",
            nargs="+",
            type=int,
            help="Optional list of fonds ids to process via archival_unit.fonds.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which records would be processed without minting ARKs.",
        )
        parser.add_argument(
            "--sleep-ms",
            type=int,
            default=250,
            help="Milliseconds to wait between mint requests. Default: 250.",
        )

    def handle(self, *args, **options):
        model_name = options["model"]
        ids = options.get("ids")
        fonds = options.get("fonds")
        dry_run = options["dry_run"]
        sleep_ms = max(options["sleep_ms"], 0)

        total_processed = 0
        total_created = 0

        if model_name in ("all", "finding_aids"):
            processed, created = self._handle_queryset(
                label="finding_aids",
                queryset=FindingAidsEntity.objects.filter(published=True, is_template=False).filter(Q(ark__isnull=True) | Q(ark="")),
                ids=ids,
                fonds=fonds,
                dry_run=dry_run,
                sleep_ms=sleep_ms,
            )
            total_processed += processed
            total_created += created

        if model_name in ("all", "isad"):
            processed, created = self._handle_queryset(
                label="isad",
                queryset=Isad.objects.filter(published=True).filter(Q(ark__isnull=True) | Q(ark="")),
                ids=ids,
                fonds=fonds,
                dry_run=dry_run,
                sleep_ms=sleep_ms,
            )
            total_processed += processed
            total_created += created

        self.stdout.write(
            self.style.SUCCESS(
                "Processed %s record(s); created %s ARK(s)." % (total_processed, total_created)
            )
        )

    def _handle_queryset(self, label, queryset, ids=None, fonds=None, dry_run=False, sleep_ms=0):
        if ids:
            queryset = queryset.filter(id__in=ids)
        if fonds:
            queryset = queryset.filter(archival_unit__fonds__in=fonds)

        processed = 0
        created = 0

        for instance in queryset.iterator():
            processed += 1
            identifier = getattr(instance, "archival_reference_code", None) or getattr(instance, "reference_code", None)

            if dry_run:
                self.stdout.write("[%s] would mint ARK for id=%s (%s)" % (label, instance.id, identifier))
                continue

            ark = ensure_ark(instance)
            if ark:
                created += 1
                self.stdout.write("[%s] minted %s for id=%s (%s)" % (label, ark, instance.id, identifier))
                if sleep_ms:
                    time.sleep(sleep_ms / 1000)
            else:
                self.stdout.write(
                    self.style.WARNING("[%s] failed to mint ARK for id=%s (%s)" % (label, instance.id, identifier))
                )
                if sleep_ms:
                    time.sleep(sleep_ms / 1000)

        return processed, created
