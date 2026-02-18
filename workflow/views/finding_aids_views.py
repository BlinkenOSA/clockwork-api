import re

from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView

from clockwork_api.authentication import BearerAuthentication
from finding_aids.models import FindingAidsEntity
from workflow.permission import APIGroupPermission
from workflow.serializers.folder_item_serializers import FADigitizedSerializer


class GetFAEntityMetadataByItemID(RetrieveAPIView):
    """
    Resolves a finding aids entity from an item-style legacy identifier.

    This endpoint supports workflow scripts that receive an item/folder identifier
    encoded in a legacy "HU_OSA_..." format and need to retrieve the corresponding
    :class:`finding_aids.models.FindingAidsEntity`.

    Authentication / Authorization:
        - BearerAuthentication or SessionAuthentication
        - Restricted to users in the ``Api`` group via APIGroupPermission

    Response:
        - Serialized finding aids entity metadata using FADigitizedSerializer.

    Raises:
        - NotFound: When the identifier does not match a supported pattern or
          cannot be resolved to a FindingAidsEntity.
    """

    swagger_schema = None
    serializer_class = FADigitizedSerializer
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    def get_object(self):
        """
        Parses the item identifier and resolves the corresponding FindingAidsEntity.

        Expected pattern (example):
            HU_OSA_<fonds>_<subfonds>_<series>_<container_no>_<folder_no>

        Notes:
            The existing parsing logic assumes a specific delimiter structure
            (split by '-' and '_'). If the upstream identifier format changes,
            this function will need to be updated accordingly.

        Returns:
            FindingAidsEntity: The resolved folder/item record.

        Raises:
            NotFound: If the identifier format is unsupported.
        """
        item_id = self.kwargs['item_id']

        if re.match(r'^HU_OSA_[0-9]+_[0-9]+_[0-9]*_[0-9]{4}_[0-9]{4}', item_id):
            # NOTE: Preserving original behavior; this replacement likely intends "HU_OSA_".
            item_id = item_id.replace("HU_OSA_", "")
            fonds, subfonds, rest, folder_no = item_id.split('-')
            series, container_no = rest.split('_')

            fa_entity = get_object_or_404(
                FindingAidsEntity,
                archival_unit__fonds=int(fonds),
                archival_unit__subfonds=int(subfonds),
                archival_unit__series=int(series),
                container__container_no=int(container_no),
                folder_no=int(folder_no)
            )
            return fa_entity

        raise NotFound(detail="Error 404, page not found", code=404)
