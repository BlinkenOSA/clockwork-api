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
            "--dry-run",
            action="store_true",
            help="Show which records would be processed without minting ARKs.",
        )

    def handle(self, *args, **options):
        model_name = options["model"]
        ids = options.get("ids")
        dry_run = options["dry_run"]

        total_processed = 0
        total_created = 0

        if model_name in ("all", "finding_aids"):
            processed, created = self._handle_queryset(
                label="finding_aids",
                queryset=FindingAidsEntity.objects.filter(published=True).filter(Q(ark__isnull=True) | Q(ark="")),
                ids=ids,
                dry_run=dry_run,
            )
            total_processed += processed
            total_created += created

        if model_name in ("all", "isad"):
            processed, created = self._handle_queryset(
                label="isad",
                queryset=Isad.objects.filter(published=True).filter(Q(ark__isnull=True) | Q(ark="")),
                ids=ids,
                dry_run=dry_run,
            )
            total_processed += processed
            total_created += created

        self.stdout.write(
            self.style.SUCCESS(
                "Processed %s record(s); created %s ARK(s)." % (total_processed, total_created)
            )
        )

    def _handle_queryset(self, label, queryset, ids=None, dry_run=False):
        if ids:
            queryset = queryset.filter(id__in=ids)

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
            else:
                self.stdout.write(
                    self.style.WARNING("[%s] failed to mint ARK for id=%s (%s)" % (label, instance.id, identifier))
                )

        return processed, created
