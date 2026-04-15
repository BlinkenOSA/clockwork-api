import urllib

import meilisearch
import pysolr
from clockwork_api.http import get
from django.conf import settings
from django.utils.html import strip_tags
from hashids import Hashids
from langdetect import detect, LangDetectException
from requests.auth import HTTPBasicAuth

from digitization.models import DigitalVersion
from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator
from finding_aids.models import FindingAidsEntity


class FindingMeilisearchIndexer:
    """
    Class to index Finding Aids records to Solr for the catalog.
    """

    def __init__(self, finding_aids_entity_id):
        self.finding_aids_entity_id = finding_aids_entity_id
        self.finding_aids_entity = self._get_finding_aids_record(finding_aids_entity_id)
        self.hashids = Hashids(salt="osacontent", min_length=10)

        self.meilisearch_url = getattr(settings, "MEILISEARCH_URL", "")
        self.meilisearch_api_key = getattr(settings, "MEILISEARCH_API_KEY", "")
        self.meilisearch_index = getattr(settings, "MEILISEARCH_INDEX", "meilisearch")

        self.client = meilisearch.Client(self.meilisearch_url, self.meilisearch_api_key)
        self.meilisearch_index = self.client.index(self.meilisearch_index)
        self.locales = ['en', 'hu', 'ru', 'pl']
        self.doc = {}

    def index(self):
        self._index_record()
        self._remove_duplicates()
        try:
            self.meilisearch_index.add_documents([self.doc])
        except Exception as e:
            print('Error with Finding Aids Report %s! Error: %s' % (self.doc['id'], e))

    def delete(self):
        self.meilisearch_index.delete_document(document_id=self._get_meilisearch_id())

    def _get_finding_aids_record(self, finding_aids_entity_id):
        qs = FindingAidsEntity.objects.filter(pk=finding_aids_entity_id)
        qs = qs.select_related('archival_unit')
        qs = qs.select_related('container')
        qs = qs.select_related('original_locale')
        qs = qs.select_related('primary_type')
        return qs.get()

    def _index_record(self):
        self.doc['id'] = self._get_meilisearch_id()
        self.doc['ams_id'] = f"finding-aids-{self.finding_aids_entity.id}"
        self.doc['archival_unit_id'] = f"{self.finding_aids_entity.archival_unit.id}"
        self.doc['series_reference_code'] = self.finding_aids_entity.archival_unit.reference_code
        self.doc['reference_code'] = self.finding_aids_entity.archival_reference_code
        self.doc['published'] = self.finding_aids_entity.published

        # Display field
        self.doc['title'] = self.finding_aids_entity.title
        self.doc['record_type'] = "Finding Aids"
        self.doc['primary_type'] = "%s" % self.finding_aids_entity.primary_type.type if self.finding_aids_entity.primary_type else None
        self.doc['description_level'] = self._get_description_level()

        # Title fields
        if self.finding_aids_entity.title_original:
            self.doc['title_original'] = self.finding_aids_entity.title_original

        # Contents Summary
        self.doc['contents_summary'] = strip_tags(self.finding_aids_entity.contents_summary)
        if self.finding_aids_entity.contents_summary_original:
            self.doc['contents_summary_original'] = strip_tags(self.finding_aids_entity.contents_summary_original)

    def _get_meilisearch_id(self):
        if self.finding_aids_entity.catalog_id:
            return self.finding_aids_entity.catalog_id
        else:
            return self.hashids.encode(self.finding_aids_entity.id)

    def _get_description_level(self):
        if self.finding_aids_entity.level == 'F':
            return 'Folder'
        else:
            return 'Item'

    def _remove_duplicates(self):
        for k, v in self.doc.items():
            if isinstance(v, list):
                if len(v) > 0:
                    if isinstance(v[0], str):
                        self.doc[k] = list(set(v))
                    else:
                        try:
                            self.doc[k] = [dict(t) for t in {tuple(d.items()) for d in v}]
                        except AttributeError:
                            pass
