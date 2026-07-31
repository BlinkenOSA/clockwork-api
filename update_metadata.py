import json
import os
import re

import requests
from office365.runtime.client_request_exception import ClientRequestException

from office365.sharepoint.client_context import ClientContext
from dotenv import load_dotenv

from office365.sharepoint.fields.url_value import FieldUrlValue

load_dotenv()

# ENV variables
collection = 'HU OSA 394/HU OSA 394-0-1'
extension = '.mp4'

site_url = os.getenv('SHAREPOINT_SITE')
library = os.getenv('DOCUMENT_LIBRARY')
input_folder = os.getenv('INPUT_DIR')
container_api = os.getenv('AMS_CONTAINER_DATA_API')
item_api = os.getenv('AMS_ITEM_DATA_API')
token = os.getenv('AMS_API_KEY')
error_folder = os.getenv('ERROR_DIR')
success_folder = os.getenv('SUCCESS_DIR')

cert_settings = {
    'client_id': os.getenv('CLIENT_ID'),
    'thumbprint': os.getenv('THUMBPRINT'),
    'cert_path': '{0}/selfsigncert.pem'.format(os.path.dirname(__file__)),
    'scopes': ['{0}.default'.format(os.getenv('SHAREPOINT_ROOT'))]
}

def try_get_folder(ctx, url):
    try:
        return ctx.web.get_folder_by_server_relative_url(url).get().execute_query()
    except ClientRequestException as e:
        if e.response.status_code == 404:
            return None
        else:
            raise ValueError(e.response.text)


def get_metadata(file_name):
    legacy_id = file_name.replace(extension, "")

    # Request info from AMS
    headers = {"Authorization": "Bearer %s" % token}

    # Container exists
    if re.match(r'^HU_OSA_[0-9]{8}', legacy_id):
        r = requests.get("%s%s" % (container_api, legacy_id), headers=headers)
    else:
        r = requests.get("%s%s" % (container_api, legacy_id), headers=headers)

    if r.status_code == 200:
        data = json.loads(r.text)
        return data


def main():
    ctx = ClientContext(site_url).with_client_certificate(os.getenv('TENANT'), **cert_settings)
    url = "%s/%s" % (library, collection)

    folder = try_get_folder(ctx, url)
    if folder is None:
        print("Folder not found")
    else:
        files = folder.files
        ctx.load(files)
        ctx.execute_query()
        for file in files:
            file_name = file.properties["Name"]
            metadata = get_metadata(file_name)

            filemeta = file.listItemAllFields

            if metadata:
                # Update metadata
                series = metadata['archival_unit']['series']

                filemeta.set_property('ArchivalReferenceNumber', '%s:%s' % (
                    series['reference_code'], metadata['container_no']
                ))
                filemeta.set_property('Description', '%s #%s' % (metadata['carrier_type'], metadata['container_no']))

                field_url = FieldUrlValue(
                    url='https://catalog.archivum.org/catalog/?tab=content&start=%s' % metadata['container_no'],
                    description='View in Catalog'
                )
                filemeta.set_property('Catalog', field_url)
                filemeta.update().execute_query()

                print('%s metadata was updated' % file_name)
            else:
                print('No metadata available for the file: %s' % file_name)


if __name__ == "__main__":
    main()