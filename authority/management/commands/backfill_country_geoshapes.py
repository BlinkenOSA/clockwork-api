from django.core.management import BaseCommand
from django.utils import timezone

from authority.models import Country
from authority.services.wikidata_cache import get_wikidata_entity_payload


class Command(BaseCommand):
    help = "Populate missing country geoshapes in cached Wikidata payloads."

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            type=int,
            help="Limit backfill to a single country primary key.",
        )

    def handle(self, *args, **options):
        record_id = options["id"]

        queryset = Country.objects.exclude(wikidata_id__isnull=True).exclude(wikidata_id="")
        if record_id is not None:
            queryset = queryset.filter(pk=record_id)

        updated = 0
        skipped = 0
        failed = 0

        for record in queryset.iterator():
            properties = (record.wikidata_cache or {}).get("properties") or {}
            if properties.get("geoshape"):
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Country #{record.pk} ({record.wikidata_id}) already has geoshape"
                    )
                )
                continue

            try:
                payload = get_wikidata_entity_payload(record.wikidata_id)
            except Exception as exc:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Country #{record.pk} ({record.wikidata_id}) failed: {exc}"
                    )
                )
                continue

            if not payload:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Country #{record.pk} ({record.wikidata_id}) returned no payload"
                    )
                )
                continue

            payload = Country.normalize_wikidata_payload(payload)
            if not (payload.get("properties") or {}).get("geoshape"):
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Country #{record.pk} ({record.wikidata_id}) still has no geoshape"
                    )
                )
                continue

            Country.objects.filter(pk=record.pk).update(
                wikidata_cache=payload,
                wikidata_cache_updated_at=timezone.now(),
            )
            updated += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Country #{record.pk} ({record.wikidata_id}) geoshape updated"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated={updated}, Skipped={skipped}, Failed={failed}"
            )
        )
