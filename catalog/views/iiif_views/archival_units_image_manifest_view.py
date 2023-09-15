import urllib

from django.conf import settings
from iiif_prezi.factory import ManifestFactory
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class ArchivalUnitsManifestView(APIView):
    permission_classes = []

    def get(self, request, archival_unit_id, *args, **kwargs):
        isad = get_object_or_404(Isad, archival_unit__id=archival_unit_id, published=True)

        factory = ManifestFactory()
        factory.set_base_prezi_uri("%s%s" % (settings.BASE_URL, request.get_full_path()))

        # Default Image API information
        factory.set_base_image_uri(getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/'))
        factory.set_iiif_image_info(2.0, 2)
        factory.set_debug("error")

        manifest = factory.manifest(label=isad.archival_unit.title_full)
        manifest.viewingDirection = "left-to-right"
        manifest.attribution = '%s<br/>' % isad.archival_unit.title_full + \
                               'Vera & Donald Blinken Open Society Archives'

        seq = manifest.sequence(label="Sequence")

        for fa_entity in FindingAidsEntity.objects.filter(archival_unit=isad.archival_unit, digital_version_online=True):
            if fa_entity.primary_type.type == 'Still Image':

                archival_unit_ref_code = fa_entity.archival_unit.reference_code.replace(" ", "_")
                item_reference_code = "%s-%04d-%03d" % (
                    archival_unit_ref_code,
                    fa_entity.container.container_no,
                    fa_entity.folder_no
                )

                image_id = 'catalog/%s/%s.jpg' % (archival_unit_ref_code, item_reference_code)
                image_id = urllib.parse.quote_plus(image_id)

                cvs = seq.canvas(ident=fa_entity.archival_reference_code, label="%s %s" % (fa_entity.archival_reference_code, fa_entity.title))
                cvs.set_image_annotation(image_id, iiif=True)

        return Response(manifest.toJSON())
