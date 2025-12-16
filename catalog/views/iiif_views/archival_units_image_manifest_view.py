"""
IIIF Image API manifest view for archival units.

This module exposes a read-only endpoint that generates a IIIF Presentation
manifest for all digitized still images belonging to a single archival unit.

The manifest is consumed by IIIF-compatible viewers in the public catalog
to enable browsing, zooming, and sequencing of digitized materials.

This view intentionally:
    - Includes only published archival units
    - Includes only finding aids entities with online digital versions
    - Generates manifests dynamically (not stored)
    - Uses IIIF Presentation API v2 semantics via iiif-prezi
"""
import urllib

from django.conf import settings
from iiif_prezi.factory import ManifestFactory
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class ArchivalUnitsManifestView(APIView):
    """
    Returns a IIIF Presentation manifest for an archival unit.

    This endpoint generates a IIIF manifest containing all still-image
    digital objects associated with a given archival unit.

    Design decisions:
        - The archival unit is resolved via its published ISAD record
        - Only still images are included in the manifest
        - Image identifiers are constructed deterministically from
          archival reference codes
        - The manifest is generated on-the-fly for freshness

    This view serves as the IIIF entry point for archival unit–level
    image galleries in the public catalog.
    """

    permission_classes = []

    def get(self, request, archival_unit_id: str, *args, **kwargs) -> Response:
        """
        Generates and returns a IIIF manifest for an archival unit.

        Args:
            archival_unit_id:
                Primary key of the archival unit.

        Returns:
            HTTP 200 response containing a IIIF Presentation manifest (JSON).

        Raises:
            Http404 if no published ISAD record exists for the archival unit.
        """
        isad = get_object_or_404(Isad, archival_unit__id=archival_unit_id, published=True)

        factory = ManifestFactory()
        factory.set_base_prezi_uri("%s%s" % (settings.BASE_URL, request.get_full_path()))

        # Default Image API information
        factory.set_base_image_uri(getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/'))
        factory.set_iiif_image_info(2.0, 2)
        factory.set_debug("error")

        # Manifest metadata
        manifest = factory.manifest(label=isad.archival_unit.title_full)
        manifest.viewingDirection = "left-to-right"
        manifest.attribution = '%s<br/>' % isad.archival_unit.title_full + \
                               'Vera & Donald Blinken Open Society Archives'

        # Sequence construction
        seq = manifest.sequence(label="Sequence")

        # Canvas generation
        for fa_entity in FindingAidsEntity.objects.filter(archival_unit=isad.archival_unit, digital_version_online=True):
            if fa_entity.primary_type.type == 'Still Image':

                # Image identifier construction
                archival_unit_ref_code = fa_entity.archival_unit.reference_code.replace(" ", "_")
                item_reference_code = "%s-%04d-%03d" % (
                    archival_unit_ref_code,
                    fa_entity.container.container_no,
                    fa_entity.folder_no
                )

                # Canvas creation
                image_id = 'catalog/%s/%s.jpg' % (archival_unit_ref_code, item_reference_code)
                image_id = urllib.parse.quote_plus(image_id)

                cvs = seq.canvas(ident=fa_entity.archival_reference_code, label="%s %s" % (fa_entity.archival_reference_code, fa_entity.title))
                cvs.set_image_annotation(image_id, iiif=True)

        return Response(manifest.toJSON())
