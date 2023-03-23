from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response

from isad.indexers.isad_catalog_indexer import ISADCatalogIndexer
from isad.indexers.isad_indexer import ISADIndexer


class IsadIndexTestView(generics.RetrieveAPIView):
    """
        Returns report solr document.
    """
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        target = self.kwargs.get("target")
        try:
            indexer = ISADCatalogIndexer(isad_id=pk)
            indexer.create_solr_document()
            return Response(indexer.get_solr_document())
        except ObjectDoesNotExist:
            return Response(status=404)
