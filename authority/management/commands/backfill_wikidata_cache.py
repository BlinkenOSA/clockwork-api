from django.core.management import BaseCommand, CommandError
from django.utils import timezone

from authority.models import Country, Language, Place, Person, Corporation, Genre, Subject
from authority.services.wikidata_cache import get_wikidata_entity_payload

AUTHORITY_MODELS = (
    Country,
    Language,
    Place,
    Person,
    Corporation,
    Genre,
    Subject,
)

AUTHORITY_MODEL_MAP = {
    model.__name__.lower(): model for model in AUTHORITY_MODELS
}


class Command(BaseCommand):
    help = "Populate cached Wikidata payloads for authority records that already have wikidata_id values."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Refresh cache fields even when a cached payload already exists.",
        )
        parser.add_argument(
            "--model",
            choices=sorted(AUTHORITY_MODEL_MAP.keys()),
            help="Limit backfill to a single authority model.",
        )
        parser.add_argument(
            "--id",
            type=int,
            help="Limit backfill to a single record primary key. Requires --model.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        model_name = options["model"]
        record_id = options["id"]

        if record_id is not None and not model_name:
            raise CommandError("--id requires --model.")

        models = [AUTHORITY_MODEL_MAP[model_name]] if model_name else list(AUTHORITY_MODELS)
        updated = 0
        skipped = 0
        failed = 0

        for model in models:
            queryset = model.objects.exclude(wikidata_id__isnull=True).exclude(wikidata_id="")
            if not force:
                queryset = queryset.filter(wikidata_cache__isnull=True)
            if record_id is not None:
                queryset = queryset.filter(pk=record_id)

            for record in queryset.iterator():
                try:
                    payload = get_wikidata_entity_payload(record.wikidata_id)
                except Exception as exc:
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"{model.__name__} #{record.pk} ({record.wikidata_id}) failed: {exc}"
                        )
                    )
                    continue

                if not payload:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"{model.__name__} #{record.pk} ({record.wikidata_id}) returned no payload"
                        )
                    )
                    continue

                model.objects.filter(pk=record.pk).update(
                    wikidata_cache=payload,
                    wikidata_cache_updated_at=timezone.now(),
                )
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{model.__name__} #{record.pk} ({record.wikidata_id}) cache updated"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated={updated}, Skipped={skipped}, Failed={failed}"
            )
        )
