import os
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import BaseCommand
from office365.sharepoint.client_context import ClientContext
from pathlib import Path

from container.models import Container
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def handle(self, *args, **options):
        site_url = getattr(settings, 'SHAREPOINT_SITE')
        doc_lib = getattr(settings, 'SHAREPOINT_DOCUMENT_LIBRARY')
        cert_settings = {
            'client_id': getattr(settings, 'SHAREPOINT_CLIENT_ID'),
            'thumbprint': getattr(settings, 'SHAREPOINT_THUMBPRINT'),
            'cert_path': os.path.join(os.path.abspath(os.path.dirname(__file__)), 'certificate.pem'),
            'scopes': ['{0}.default'.format(getattr(settings, 'SHAREPOINT_ROOT'))]
        }
        ctx = ClientContext(site_url).with_client_certificate(getattr(settings, 'SHAREPOINT_TENANT'), **cert_settings)
        root_folder = ctx.web.get_folder_by_server_relative_path(doc_lib)

        folders = root_folder.expand(["Folders"]).get().execute_query()

        for f in folders.folders:
            if "HU OSA" in f.name:
                if f.name != 'HU OSA 320' and f.name != 'HU OSA 440' and f.name != 'HU OSA 362':
                    folder = ctx.web.get_folder_by_server_relative_path("%s/%s" % (doc_lib, f.name))
                    files = folder.get_files(True).execute_query()

                    for file in files:
                        file_url = file.serverRelativeUrl
                        string_to_replace = "/sites/osa-researchcloud/%s/" % doc_lib
                        file_url = file_url.replace(string_to_replace, "")
                        self.save_metadata(file_url)

    def save_metadata(self, file_url):
        record = None
        name = Path(file_url).stem

        # Check if name is a barcode
        if re.match(r'^HU_OSA_[0-9]{8}$', name):
            try:
                record = Container.objects.get(barcode=name)
            except ObjectDoesNotExist:
                pass

        # Check if name is in a legacy format container level
        if re.match(r'^HU OSA [0-9]+-[0-9]+-[0-9]*_[0-9]{3}$', name):
            code = name.replace("HU OSA ", "")
            fonds, subfonds, rest = code.split('-')
            series, container_no = rest.split('_')
            try:
                record = Container.objects.get(
                    archival_unit__fonds=fonds,
                    archival_unit__subfonds=subfonds,
                    archival_unit__series=series,
                    container_no=container_no
                )
            except ObjectDoesNotExist:
                pass

        # Check if name is in a legacy format folder/item level
        if re.match(r'^HU OSA [0-9]+-[0-9]+-[0-9]*_[0-9]{3}-[0-9]{3}$', name):
            code = name.replace("HU OSA ", "")
            fonds, subfonds, rest, folder_no = code.split('-')
            series, container_no = rest.split('_')
            try:
                record = FindingAidsEntity.objects.get(
                    archival_unit__fonds=int(fonds),
                    archival_unit__subfonds=int(subfonds),
                    archival_unit__series=int(series),
                    container__container_no=int(container_no),
                    folder_no=int(folder_no),
                )
            except ObjectDoesNotExist:
                pass

        if record:
            print("%s record was updated with Research Cloud data!" % name)
            record.digital_version_exists = True
            record.digital_version_research_cloud = True
            record.digital_version_research_cloud_path = file_url
            record.save()
        else:
            try:
                # Check container legacy id
                record = Container.objects.get(
                    legacy_id=name
                )
                record.digital_version_exists = True
                record.digital_version_research_cloud = True
                record.digital_version_research_cloud_path = file_url
                record.save()
            except ObjectDoesNotExist:
                records = FindingAidsEntity.objects.filter(
                    legacy_id=name
                )
                if records.count() == 0:
                    print("I can't find matching records for: %s" % name)
                else:
                    for record in records.all():
                        print("%s record was updated with Research Cloud data!" % name)
                        record.container.legacy_id = name
                        record.container.digital_version_exists = True
                        record.container.digital_version_research_cloud = True
                        record.container.digital_version_research_cloud_path = file_url
                        record.save()