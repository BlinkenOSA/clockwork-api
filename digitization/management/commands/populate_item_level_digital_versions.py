from django.core.management import BaseCommand

from digitization.models import DigitalVersion
from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.create_access_copies()

    def create_access_copies(self):
        for fa_entity in FindingAidsEntity.objects.filter(digital_version_exists=True, is_template=False):
            identifier = DigitalVersionIdentifierGenerator(fa_entity).generate_identifier()
            extension = ''

            if fa_entity.primary_type.type == 'Textual':
                extension = 'pdf'

            if fa_entity.primary_type.type == 'Still Image':
                extension = 'jpg'

            if fa_entity.primary_type.type == 'Moving Image':
                extension = 'mp4'

            if fa_entity.primary_type.type == 'Audio':
                extension = 'mp3'

            # Create entry for access files
            digital_version, created = DigitalVersion.objects.get_or_create(
                finding_aids_entity=fa_entity,
                identifier=identifier,
                level='A'
            )
            digital_version.filename = "%s.%s" % (identifier, extension)
            digital_version.creation_date = fa_entity.digital_version_creation_date
            digital_version.technical_metadata = fa_entity.digital_version_technical_metadata
            digital_version.available_online = fa_entity.digital_version_online
            digital_version.available_research_cloud = fa_entity.digital_version_research_cloud
            digital_version.research_cloud_path = fa_entity.digital_version_research_cloud_path
            digital_version.save()
