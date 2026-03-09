import csv
import os
from collections import defaultdict

from django.core.management import BaseCommand
from django.db.models import Count

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    help = (
        "Export a CSV for all series-level archival units with container counts grouped by "
        "carrier type and finding aids record counts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            dest="output",
            default="series_container_finding_aids_statistics.csv",
            help="Output CSV file path.",
        )

    def handle(self, *args, **options):
        output_path = os.path.abspath(options["output"])

        series_units = list(
            ArchivalUnit.objects.filter(level="S")
            .select_related("parent", "parent__parent")
            .order_by("sort")
        )

        container_rows = (
            Container.objects.filter(archival_unit__level="S")
            .values("archival_unit_id", "carrier_type__type")
            .annotate(total=Count("id"))
            .order_by("carrier_type__type")
        )

        containers_by_series = defaultdict(list)
        for row in container_rows:
            containers_by_series[row["archival_unit_id"]].append(
                (row["carrier_type__type"], row["total"])
            )

        fa_counts = {
            row["archival_unit_id"]: row["total"]
            for row in (
                FindingAidsEntity.objects.filter(archival_unit__level="S", is_template=False)
                .values("archival_unit_id")
                .annotate(total=Count("id"))
            )
        }

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "Fonds",
                    "Subfonds",
                    "Series",
                    "Number of containers (multi-line)",
                    "Number of Finding Aids records",
                ]
            )

            for series in series_units:
                fonds = series.get_fonds()
                subfonds = series.parent if series.parent and series.parent.level == "SF" else None

                fonds_label = f"{fonds.reference_code} {fonds.title}" if fonds else ""
                subfonds_label = (
                    f"{subfonds.reference_code} {subfonds.title}" if subfonds else ""
                )
                series_label = f"{series.reference_code} {series.title}"

                grouped_container_counts = containers_by_series.get(series.id, [])
                if grouped_container_counts:
                    container_counts_text = "\n".join(
                        f"{carrier_type}: {count}"
                        for carrier_type, count in grouped_container_counts
                    )
                else:
                    container_counts_text = "0"

                writer.writerow(
                    [
                        fonds_label,
                        subfonds_label,
                        series_label,
                        container_counts_text,
                        fa_counts.get(series.id, 0),
                    ]
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"CSV export complete: {output_path} ({len(series_units)} series rows)"
            )
        )
