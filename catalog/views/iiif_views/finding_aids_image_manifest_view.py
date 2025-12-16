"""
IIIF Presentation API v2 manifest view for a single finding aids entity image.

This module exposes a minimal IIIF v2 manifest for a single still-image
FindingAidsEntity. Unlike the v3 presentation view, this endpoint:

    - Uses IIIF Presentation API v2
    - Generates exactly one canvas
    - Is optimized for simple viewers and legacy integrations
    - Uses iiif-prezi (v2) rather than iiif-prezi3

This view exists alongside the v3 endpoint to support older IIIF clients
and embedded viewers that do not yet support IIIF Presentation v3.
"""
import urllib

from django.conf import settings
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory
from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity


class FindingAidsImageManifestView(APIView):
    """
    Returns a IIIF Presentation API v2 manifest for a single still image.

    This endpoint generates a minimal IIIF v2 manifest containing
    a single canvas for a finding aids entity that represents
    a digitized still image.

    Typical use cases:
        - legacy IIIF viewers
        - simple image embeds
        - lightweight gallery components

    The manifest is generated dynamically and is not persisted.
    """

    permission_classes = []

    def get(self, request, fa_entity_catalog_id: str, *args, **kwargs) -> Response:
        """
        Generates and returns a IIIF v2 manifest for a finding aids entity.

        Args:
            fa_entity_catalog_id:
                Public catalog identifier of the finding aids entity.

        Returns:
            HTTP 200 response containing a IIIF Presentation v2 manifest (JSON),
            or HTTP 404 if the entity is not a viewable still image.
        """
        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=fa_entity_catalog_id)

        # Eligibility check
        if fa_entity.primary_type.type == 'Still Image' and fa_entity.available_online:

            # IIIF v2 manifest factory setup
            factory = ManifestFactory()
            factory.set_base_prezi_uri("%s%s" % (settings.BASE_URL, request.get_full_path().replace('manifest.json', '')))

            # Default IIIF Image API configuration
            factory.set_base_image_uri(getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/'))
            factory.set_iiif_image_info(2.0, 2)
            factory.set_debug("error")

            # Manifest metadata
            manifest = factory.manifest(label="%s %s" % (fa_entity.archival_reference_code, fa_entity.title))
            manifest.viewingDirection = "left-to-right"
            manifest.attribution = '%s %s<br/>' % (fa_entity.archival_reference_code, fa_entity.title) + \
                                   '%s<br/>' % fa_entity.archival_unit.title_full + \
                                   'Vera & Donald Blinken Open Society Archives'

            # Sequence and canvas construction
            seq = manifest.sequence()

            # Stable image identifier construction
            archival_unit_ref_code = fa_entity.archival_unit.reference_code.replace(" ", "_")
            item_reference_code = "%s_%04d_%04d" % (
                archival_unit_ref_code,
                fa_entity.container.container_no,
                fa_entity.folder_no
            )

            # Canvas creation
            image_id = 'catalog/%s/%s.jpg' % (archival_unit_ref_code, item_reference_code)
            image_id = urllib.parse.quote_plus(image_id)

            cvs = seq.canvas(ident='Image', label="Image")
            cvs.set_image_annotation(image_id, iiif=True)

            return Response(manifest.toJSON(top=True))
        else:
            # Non-image fallback
            return Response(data={'Record is not an image, or not available online!'}, status=404)
