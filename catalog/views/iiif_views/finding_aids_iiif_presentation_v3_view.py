import json
import urllib

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from iiif_prezi3 import Manifest
from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity


class FindingAidsIIFPresentationV3View(APIView):
    permission_classes = []

    def get(self, request, fa_entity_catalog_id, *args, **kwargs):
        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=fa_entity_catalog_id)

        if fa_entity.primary_type.type == 'Still Image' and fa_entity.available_online:
            base_image_url = getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/')

            manifest = Manifest(
                id="%s%s" % (settings.BASE_URL, request.get_full_path()),
                label='%s %s<br/>' % (fa_entity.archival_reference_code, fa_entity.title) +
                      '%s<br/>' % fa_entity.archival_unit.title_full + 'Blinken OSA Archivum'
            )

            for digital_version in fa_entity.digitalversion_set.all().order_by('identifier'):
                main_directory = "_".join(digital_version.identifier.split("_", 5)[:5])

                image_id = "catalog/%s/%s" % (main_directory, digital_version.filename)
                image_id = urllib.parse.quote_plus(image_id)
                url = "%s%s" % (base_image_url, image_id)

                label = digital_version.label if digital_version.label else "Image"

                try:
                    canvas = manifest.make_canvas_from_iiif(
                        url=url,
                        label=label
                    )

                    canvas.add_thumbnail(
                        image_url="%s/full/,300/0/default.jpg" % url
                    )
                except requests.exceptions.HTTPError:
                    pass

            response = json.loads(manifest.json(indent=4))

            return Response(response)
        else:
            return Response(data={'Record is not an image, or not available online!'}, status=404)
