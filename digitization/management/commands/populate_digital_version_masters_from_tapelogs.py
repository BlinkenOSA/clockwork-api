from pathlib import Path

from django.core.management import BaseCommand
from django.db import transaction

from container.models import Container
from digitization.models import DigitalVersion, DigitalVersionPhysicalCopy


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Optional override path to tapelogs directory",
        )
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Parse files but do not create records",
        )

    def handle(self, *args, **options):
        # Default directory: alongside this command, in tapelogs/
        if options["path"]:
            tapelogs_dir = Path(options["path"]).expanduser().resolve()
        else:
            tapelogs_dir = Path(__file__).resolve().parent / "tapelogs"

        if not tapelogs_dir.exists() or not tapelogs_dir.is_dir():
            raise FileNotFoundError(f"Tapelogs directory not found: {tapelogs_dir}")

        dry_run = options["dry_run"]

        created = 0
        missing_containers = 0
        skipped_empty = 0

        txt_files = sorted(tapelogs_dir.glob("*.txt"))
        if not txt_files:
            self.stdout.write(self.style.WARNING(f"No .txt files found in {tapelogs_dir}"))
            return

        self.stdout.write(f"Reading {len(txt_files)} file(s) from {tapelogs_dir}")

        with transaction.atomic():
            for file_path in txt_files:
                label_of_the_tape = file_path.stem
                self.stdout.write(f"Processing: {file_path.name} (label={label_of_the_tape})")

                with open(file_path, "r", encoding="utf-16") as f:
                    for line_no, raw in enumerate(f, start=1):
                        barcode = raw.strip()

                        if not barcode or barcode == '\x00':
                            skipped_empty += 1
                            continue

                        try:
                            # "barcode as the id" => primary key lookup
                            container = Container.objects.get(barcode=barcode)
                        except Container.DoesNotExist:
                            missing_containers += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[{file_path.name}:{line_no}] Container with id={barcode!r} does not exist; skipping."
                                )
                            )
                            continue

                        if dry_run:
                            created += 1
                            continue

                        # If DigitalVersion has only barcode + storage:
                        digital_version, dv_created = DigitalVersion.objects.get_or_create(
                            container=container,
                            level='M',
                            identifier=barcode,
                            filename=f"{barcode}.avi"
                        )

                        DigitalVersionPhysicalCopy.objects.get_or_create(
                            digital_version=digital_version,
                            storage_unit='LTO-7',
                            storage_unit_label=label_of_the_tape
                        )

                        created += 1
                        print(f"Processed {digital_version.identifier} on tape {label_of_the_tape}")
                    # end for each line
                # end for each file

        if dry_run:
            transaction.set_rollback(True)

        msg = f"Done. Would create {created} records." if dry_run else f"Done. Created {created} records."
        if missing_containers:
            msg += f" Missing containers: {missing_containers}."
        if skipped_empty:
            msg += f" Skipped empty lines: {skipped_empty}."
        self.stdout.write(self.style.SUCCESS(msg))