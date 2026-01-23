from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND

from isad.indexers.isad_ams_indexer import ISADAMSIndexer
from isad.indexers.isad_new_catalog_indexer import ISADNewCatalogIndexer


class IsadIndexTestView(generics.RetrieveAPIView):
    """
    Returns the generated Solr document for an ISAD record.

    This endpoint is intended for debugging and inspection of indexing output.
    It instantiates the appropriate indexer (catalog vs AMS), builds the Solr
    document in-memory, and returns the resulting document as the response
    payload.

    Notes
    -----
    This view does not write to Solr or commit changes. It only returns the
    document that *would* be indexed.

    URL Parameters
    --------------
    pk : int
        Primary key of the ISAD record to be indexed.
    target : str
        Indexing target selector:
            - ``'catalog'``: use :class:`isad.indexers.isad_new_catalog_indexer.ISADNewCatalogIndexer`
            - any other value: use :class:`isad.indexers.isad_ams_indexer.ISADAMSIndexer`

    Responses
    ---------
    200 OK
        JSON payload containing the generated Solr document.
    404 Not Found
        Returned if the ISAD record does not exist (``indexer.isad`` is falsy).
    """

    def get(self, request, *args, **kwargs):
        """
        Builds and returns the Solr document for the requested ISAD record.
        """
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
