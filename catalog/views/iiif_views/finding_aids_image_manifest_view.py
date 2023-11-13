import urllib

from django.conf import settings
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory
from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity


class FindingAidsImageManifestView(APIView):
    permission_classes = []

    def get(self, request, fa_entity_catalog_id, *args, **kwargs):
        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=fa_entity_catalog_id)

        if fa_entity.primary_type.type == 'Still Image' and fa_entity.digital_version_online:

            factory = ManifestFactory()
            factory.set_base_prezi_uri("%s%s" % (settings.BASE_URL, request.get_full_path().replace('manifest.json', '')))

            # Default Image API information
            factory.set_base_image_uri(getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/'))
            factory.set_iiif_image_info(2.0, 2)
            factory.set_debug("error")

            manifest = factory.manifest(label="%s %s" % (fa_entity.archival_reference_code, fa_entity.title))
            manifest.viewingDirection = "left-to-right"
            manifest.attribution = '%s %s<br/>' % (fa_entity.archival_reference_code, fa_entity.title) + \
                                   '%s<br/>' % fa_entity.archival_unit.title_full + \
                                   'Vera & Donald Blinken Open Society Archives'

            seq = manifest.sequence()

            archival_unit_ref_code = fa_entity.archival_unit.reference_code.replace(" ", "_")
            item_reference_code = "%s-%04d-%03d" % (
                archival_unit_ref_code,
                fa_entity.container.container_no,
                fa_entity.folder_no
            )

            image_id = 'catalog/%s/%s.jpg' % (archival_unit_ref_code, item_reference_code)
            image_id = urllib.parse.quote_plus(image_id)

            cvs = seq.canvas(ident='Image', label="Image")
            cvs.set_image_annotation(image_id, iiif=True)

            return Response(manifest.toJSON(top=True))
        else:
            return Response(data={'Record is not an image, or not available online!'}, status=404)
