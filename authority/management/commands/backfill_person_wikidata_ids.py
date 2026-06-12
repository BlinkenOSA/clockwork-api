from django.core.management import BaseCommand
from django.db.models import Q

from authority.models import Person
from authority.services.wikidata_id_lookup import resolve_person_wikidata_id


class Command(BaseCommand):
    help = (
        "Populate missing Person.wikidata_id values from stored Wikipedia and VIAF references."
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
            help="Process at most this many person records.",
        )
        parser.add_argument(
            "--id",
            type=int,
            help="Limit backfill to a single person primary key.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        record_id = options["id"]

        queryset = Person.objects.filter(
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

        for person in queryset:
            wikidata_id, meta = resolve_person_wikidata_id(
                wiki_url=person.wiki_url or "",
                authority_url=person.authority_url or "",
            )

            if meta["status"] == "conflict":
                conflicts += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Person #{person.pk} conflict: wikipedia={meta['wikipedia_id']}, viaf={meta['viaf_id']}"
                    )
                )
                continue

            if not wikidata_id:
                unresolved += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Person #{person.pk} unresolved from stored references"
                    )
                )
                continue

            if dry_run:
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Person #{person.pk} would be updated to {wikidata_id} via {meta['source']}"
                    )
                )
                continue

            person.wikidata_id = wikidata_id
            person.save()
            updated += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Person #{person.pk} updated to {wikidata_id} via {meta['source']}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated={updated}, Unresolved={unresolved}, Conflicts={conflicts}, DryRun={dry_run}"
            )
        )
