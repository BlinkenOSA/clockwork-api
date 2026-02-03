from django.core.management import BaseCommand

from container.models import Container
from digitization.models import DigitalVersion
from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.create_access_copies()
        self.create_masters()

    def create_masters(self):
        for container in Container.objects.filter(digital_version_exists=True):
            if container.barcode:
                identifier = container.barcode

                # Create entry for access files
                digital_version, created = DigitalVersion.objects.get_or_create(
                    container=container,
                    identifier=identifier,
                    level='M'
                )
                digital_version.filename = "%s.%s" % (identifier, "avi")
                digital_version.creation_date = container.digital_version_creation_date
                digital_version.available_online = False
                digital_version.available_research_cloud = False
                digital_version.save()

    def create_access_copies(self):
        for container in Container.objects.filter(digital_version_exists=True):
            if container.barcode:
                identifier = container.barcode

                # Create entry for access files
                digital_version, created = DigitalVersion.objects.get_or_create(
                    container=container,
                    identifier=identifier,
                    level='A'
                )
                digital_version.filename = "%s.%s" % (identifier, "mp4")
                digital_version.creation_date = container.digital_version_creation_date
                digital_version.technical_metadata = container.digital_version_technical_metadata
                digital_version.available_online = container.digital_version_online
                digital_version.available_research_cloud = container.digital_version_research_cloud
                digital_version.research_cloud_path = container.digital_version_research_cloud_path
                digital_version.save()
