from django.core.management import BaseCommand
from django.db import transaction

from authority.models import Person, fold, simhash64

class Command(BaseCommand):
    def handle(self, *args, **options):
        BATCH = 2000;
        buf = [];
        n = 0

        for p in Person.objects.all().only('id', 'first_name', 'last_name', 'full_name_folded', 'simhash64').iterator(
                chunk_size=BATCH):
            full = f"{(p.first_name or '').strip()} {(p.last_name or '').strip()}".strip()
            folded = fold(full)
            sh = simhash64(folded) & 0xFFFFFFFFFFFFFFFF
            if p.full_name_folded != folded or p.simhash64 != sh:
                p.full_name_folded = folded
                p.simhash64 = sh
                buf.append(p)
            if len(buf) >= BATCH:
                with transaction.atomic():
                    Person.objects.bulk_update(buf, ['full_name_folded', 'simhash64'])
                n += len(buf);
                buf = []
        if buf:
            with transaction.atomic():
                Person.objects.bulk_update(buf, ['full_name_folded', 'simhash64'])
            n += len(buf)
        print(f"✅ Backfilled {n}")