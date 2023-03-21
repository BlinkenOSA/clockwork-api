import json

import pysolr
from django.conf import settings

from isad.models import Isad
from isad.serializers.isad_ams_indexer_serializers import ISADAMSIndexerSerializer


class FindingAidsAMSIndexer:
    """
    Class to index ISAD(G) records to Solr.
    """

    def __init__(self, isad_id, target='ams'):
        self.isad_id = isad_id
        self.isad = self._get_isad(isad_id)
        self.target = target

        if self.target == 'ams':
            self.solr_core = getattr(settings, "SOLR_CORE_AMS", "ams")
        else:
            self.solr_core = getattr(settings, "SOLR_CORE_CATALOG", "catalog")

        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url)
        self.doc = {}

    def get_solr_document(self):
        return self.doc

    def index(self):
        self.create_solr_document()
        try:
            self.solr.add([self.doc])
            print("Indexing Report No. %s!" % (self.doc['id']))
        except pysolr.SolrError as e:
            print('Error with Report No. %s! Error: %s' % (self.doc['id'], e))

    def delete(self):
        self.solr.delete(id=self.isad_id, commit=True)

    def _get_isad(self, isad_id):
        qs = Isad.objects.filter(pk=isad_id)
        qs = qs.select_related('archival_unit')
        qs = qs.select_related('original_locale')
        qs = qs.select_related('access_rights')
        qs = qs.select_related('reproduction_rights')
        qs = qs.select_related('rights_restriction_reason')
        return qs.get()

    def create_solr_document(self):
        self._index_record()
        self._store_json()
        self._remove_duplicates()

    def _index_record(self):
        serializer = ISADAMSIndexerSerializer(self.isad)
        self.doc = serializer.data

    def _remove_duplicates(self):
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))

    def _store_json(self):
        pass
