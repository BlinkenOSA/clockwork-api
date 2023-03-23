from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response

from finding_aids.indexers.finding_aids_ams_indexer import FindingAidsAMSIndexer
from finding_aids.indexers.finding_aids_catalog_indexer import FindingAidsCatalogIndexer


class FindingAidsEntityIndexTestView(generics.RetrieveAPIView):
    """
        Returns report solr document.
    """
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        target = self.kwargs.get("target")
        try:
            if target == 'ams':
                indexer = FindingAidsAMSIndexer(isad_id=pk, target='ams')
            else:
                indexer = FindingAidsCatalogIndexer(finding_aids_entity_id=pk)
            indexer.create_solr_document()
            return Response(indexer.get_solr_document())
        except ObjectDoesNotExist:
            return Response(status=404)
