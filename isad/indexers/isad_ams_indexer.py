import json

import pysolr
from django.conf import settings
from hashids import Hashids

from isad.models import Isad


class ISADAMSIndexer:
    """
    Indexer for publishing ISAD(G) records to the AMS Solr index.

    This class is responsible for transforming an :class:`isad.models.Isad`
    instance into a Solr document suitable for the AMS search core and either
    indexing or removing that document.

    The indexer:
        - loads the ISAD record and related objects
        - builds a Solr-compatible document
        - handles add and delete operations against Solr
    """

    def __init__(self, isad_id):
        """
        Initializes the AMS indexer for a specific ISAD record.

        Parameters
        ----------
        isad_id : int
            Primary key of the ISAD record to be indexed.
        """
        self.isad_id = isad_id
        self.isad = self._get_isad(isad_id)
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG", "catalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, always_commit=True)
        self.doc = {}

    def get_solr_document(self):
        """
        Returns the internally generated Solr document.

        Returns
        -------
        dict
            Solr document representing the ISAD record.
        """
        return self.doc

    def index(self):
        """
        Indexes the ISAD record into the AMS Solr core.

        Builds the Solr document and attempts to add it to Solr. Errors are
        caught and logged to stdout.
        """
        self.create_solr_document()
        try:
            self.solr.add([self.doc])
            print("Indexing Report No. %s!" % (self.doc['id']))
        except pysolr.SolrError as e:
            print('Error with Report No. %s! Error: %s' % (self.doc['id'], e))

    def delete(self):
        """
        Removes the ISAD record from the AMS Solr index.
        """
        self.solr.delete(id=self.isad_id, commit=True)

    def _get_isad(self, isad_id):
        """
        Retrieves the ISAD record with related objects optimized for indexing.

        Parameters
        ----------
        isad_id : int
            Primary key of the ISAD record.

        Returns
        -------
        isad.models.Isad
            Fully populated ISAD instance.
        """
        qs = Isad.objects.filter(pk=isad_id)
        qs = qs.select_related('archival_unit')
        qs = qs.select_related('original_locale')
        qs = qs.select_related('access_rights')
        qs = qs.select_related('reproduction_rights')
        qs = qs.select_related('rights_restriction_reason')
        return qs.get()

    def create_solr_document(self):
        """
        Builds the complete Solr document for the ISAD record.

        This method orchestrates:
            - field-level indexing
            - optional JSON storage
            - duplicate value cleanup
        """
        self._index_record()
        self._store_json()
        self._remove_duplicates()

    def _index_record(self):
        """
        Populates Solr fields derived from the ISAD record.

        This includes identity fields, display fields, and hierarchical
        archival-unit-derived values.
        """
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
        """
        Computes the Solr document identifier.

        The identifier is a Hashids-encoded value derived from the fonds,
        subfonds, and series numbers of the archival unit.

        Returns
        -------
        str
            Stable Solr document identifier.
        """
        hashids = Hashids(salt="osaarchives", min_length=8)
        return hashids.encode(
            self.isad.archival_unit.fonds * 1000000 +
            self.isad.archival_unit.subfonds * 1000 +
            self.isad.archival_unit.series
        )

    def _get_description_level(self):
        """
        Returns the human-readable description level.

        Returns
        -------
        str
            One of ``'Fonds'``, ``'Subfonds'``, or ``'Series'``.
        """
        levels = {
            'F': 'Fonds',
            'SF': 'Subfonds',
            'S': 'Series'
        }
        return levels[self.isad.description_level]

    def _get_date_created_display(self):
        """
        Builds a display-friendly date range string.

        Uses ``year_from`` and ``year_to`` when available.

        Returns
        -------
        str
            Date string suitable for display and indexing.
        """
        if self.isad.year_from > 0:
            date = str(self.isad.year_from)

            if self.isad.year_to:
                if self.isad.year_from != self.isad.year_to:
                    date = date + " - " + str(self.isad.year_to)
        else:
