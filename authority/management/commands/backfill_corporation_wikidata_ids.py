from django.core.management import BaseCommand
from django.db.models import Q

from authority.models import Corporation
from authority.services.wikidata_id_lookup import resolve_corporation_wikidata_id


class Command(BaseCommand):
    help = (
        "Populate missing Corporation.wikidata_id values from stored Wikipedia and VIAF references."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Resolve and report matches without saving changes.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Process at most this many corporation records.",
        )
        parser.add_argument(
            "--id",
            type=int,
            help="Limit backfill to a single corporation primary key.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        record_id = options["id"]

        queryset = Corporation.objects.filter(
            Q(wikidata_id__isnull=True) | Q(wikidata_id="")
        ).filter(
            Q(wiki_url__isnull=False) | Q(authority_url__isnull=False)
        ).exclude(
            Q(wiki_url="") & Q(authority_url="")
        ).order_by("pk")

        if record_id is not None:
            queryset = queryset.filter(pk=record_id)
        if limit is not None:
            queryset = queryset[:limit]

        updated = 0
        unresolved = 0
        conflicts = 0

        for corporation in queryset:
            wikidata_id, meta = resolve_corporation_wikidata_id(
                wiki_url=corporation.wiki_url or "",
                authority_url=corporation.authority_url or "",
            )

            if meta["status"] == "conflict":
                conflicts += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Corporation #{corporation.pk} conflict: wikipedia={meta['wikipedia_id']}, viaf={meta['viaf_id']}"
                    )
                )
                continue

            if not wikidata_id:
                unresolved += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Corporation #{corporation.pk} unresolved from stored references"
                    )
                )
                continue

            if dry_run:
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Corporation #{corporation.pk} would be updated to {wikidata_id} via {meta['source']}"
                    )
                )
                continue

            corporation.wikidata_id = wikidata_id
            corporation.save()
            updated += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Corporation #{corporation.pk} updated to {wikidata_id} via {meta['source']}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated={updated}, Unresolved={unresolved}, Conflicts={conflicts}, DryRun={dry_run}"
            )
        )
