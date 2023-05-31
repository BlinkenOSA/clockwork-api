import json

import pysolr
from django.conf import settings
from hashids import Hashids

from isad.models import Isad


class ISADAMSIndexer:
    """
    Class to index ISAD(G) records to Solr for the AMS.
    """

    def __init__(self, isad_id):
        self.isad_id = isad_id
        self.isad = self._get_isad(isad_id)
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG", "catalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, always_commit=True)
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
        self.doc['id'] = self._get_solr_id()
        self.doc['ams_id'] = self.isad.id

        # Display field
        self.doc['record_origin'] = "Archives"
        self.doc['primary_type'] = "Archival Unit"
        self.doc['description_level'] = self._get_description_level()
        self.doc['title'] = self.isad.title
        self.doc['reference_code'] = self.isad.reference_code
        self.doc['date_created'] = self._get_date_created_display()
        self.doc['creator'] = self._get_creator()

        # Archival Unit specific display fields
        self.doc['fonds_name'] = self._get_fonds_name()
        self.doc['subfonds_name'] = self._get_subfonds_name()

    def _get_solr_id(self):
        hashids = Hashids(salt="osaarchives", min_length=8)
        return hashids.encode(
            self.isad.archival_unit.fonds * 1000000 +
            self.isad.archival_unit.subfonds * 1000 +
            self.isad.archival_unit.series
        )

    def _get_description_level(self):
        levels = {
            'F': 'Fonds',
            'SF': 'Subfonds',
            'S': 'Series'
        }
        return levels[self.isad.description_level]

    def _get_date_created_display(self):
        if self.isad.year_from > 0:
            date = str(self.isad.year_from)

            if self.isad.year_to:
                if self.isad.year_from != self.isad.year_to:
                    date = date + " - " + str(self.isad.year_to)
        else:
            date = ""
        return date

    def _get_creator(self):
        creators = list(c.creator for c in self.isad.isadcreator_set.all())
        if self.isad.isaar:
            creators.append(self.isad.isaar.name)
        return creators

    def _get_fonds_name(self):
        if self.isad.description_level == 'SF' or self.isad.description_level == 'S':
            return self.isad.archival_unit.get_fonds().title_full
        else:
            return self.isad.archival_unit.title_full

    def _get_subfonds_name(self):
        if self.isad.description_level == 'SF' or self.isad.description_level == 'S':
            return self.isad.archival_unit.get_subfonds().title_full
        else:
            return None

    def _remove_duplicates(self):
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))

    def _store_json(self):
        pass
