from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND

from isad.indexers.isad_ams_indexer import ISADAMSIndexer
from isad.indexers.isad_new_catalog_indexer import ISADNewCatalogIndexer


class IsadIndexTestView(generics.RetrieveAPIView):
    """
        Returns report solr document.
    """
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        target = self.kwargs.get("target")
        if target == 'catalog':
            indexer = ISADNewCatalogIndexer(isad_id=pk)
        else:
            indexer = ISADAMSIndexer(isad_id=pk)
        if indexer.isad:
            indexer.create_solr_document()
            return Response(indexer.get_solr_document())
        else:
            return Response(status=HTTP_404_NOT_FOUND)