"""
IIIF Presentation API v3 manifest view for individual finding aids entities.

This module exposes a IIIF Presentation v3 manifest for a single
FindingAidsEntity when it represents a digitized still image.

Unlike archival-unit–level manifests (v2), this endpoint:
    - Uses IIIF Presentation API v3
    - Targets a single finding aids entity
    - Generates one canvas per digital file
    - Is optimized for item-level viewing (deep zoom, paging)

The manifest is consumed by IIIF v3–compatible viewers in the public catalog.
"""
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
    """
    Returns a IIIF Presentation API v3 manifest for a finding aids entity.

    This view generates a IIIF v3 manifest only when:
        - the finding aids entity represents a still image
        - the image is available online

    Each associated digital file becomes its own canvas in the manifest.

    This endpoint is typically used for:
        - item-level viewers
        - deep zoom interfaces
        - mobile-friendly IIIF consumption
    """

    permission_classes = []

    def get(self, request, fa_entity_catalog_id: str, *args, **kwargs):
        """
        Generates and returns a IIIF v3 manifest for a finding aids entity.

        Args:
            fa_entity_catalog_id:
                Public catalog identifier of the finding aids entity.

        Returns:
            HTTP 200 response containing a IIIF Presentation v3 manifest (JSON),
            or HTTP 404 if the entity is not a viewable still image.
        """
        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=fa_entity_catalog_id)

        # Eligibility check
        if fa_entity.primary_type.type == 'Still Image' and fa_entity.available_online:

            # Manifest construction
            base_image_url = getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/')
            manifest = Manifest(
                id="%s%s" % (settings.BASE_URL, request.get_full_path()),
                label='%s %s<br/>' % (fa_entity.archival_reference_code, fa_entity.title) +
                      '%s<br/>' % fa_entity.archival_unit.title_full + 'Blinken OSA Archivum'
            )

            # Canvas generation per digital file
            for digital_version in fa_entity.digitalversion_set.all().order_by('filename'):

                # Image identifier resolution
                main_directory = "_".join(digital_version.identifier.split("_", 5)[:5])

                image_id = "catalog/%s/%s" % (main_directory, digital_version.filename)
                image_id = urllib.parse.quote_plus(image_id)
                url = "%s%s" % (base_image_url, image_id)

                # Canvas creation and thumbnails
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
            # Non-image fallback
            return Response(data={'Record is not an image, or not available online!'}, status=404)
