from django.core.management import BaseCommand

from research.models import Researcher


class Command(BaseCommand):
    def handle(self, *args, **options):
        for researcher in Researcher.objects.all():
            researcher.first_name = researcher.first_name.strip()
            researcher.last_name = researcher.last_name.strip()
            researcher.save()