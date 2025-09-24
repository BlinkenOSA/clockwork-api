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
    swagger_schema = None
    serializer_class = FADigitizedSerializer
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    def get_object(self):
        item_id = self.kwargs['item_id']

        if re.match(r'^HU_OSA_[0-9]+_[0-9]+_[0-9]*_[0-9]{4}_[0-9]{4}', item_id):
            item_id = item_id.replace("HU OSA ", "")
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