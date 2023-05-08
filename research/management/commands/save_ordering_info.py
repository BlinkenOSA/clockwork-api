from django.core.management import BaseCommand

from research.models import Researcher, RequestItem


class Command(BaseCommand):
    def handle(self, *args, **options):
        for request_item in RequestItem.objects.all():
            request_item.save()
