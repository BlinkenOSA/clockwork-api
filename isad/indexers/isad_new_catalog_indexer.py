import pysolr
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from hashids import Hashids
from requests.auth import HTTPBasicAuth

from isad.models import Isad


class ISADNewCatalogIndexer:
    """
    Indexer for publishing ISAD(G) records to the public catalog Solr core.

    This indexer transforms an :class:`isad.models.Isad` instance into a Solr
    document used by the "new catalog" search core and supports indexing and
    deletion operations.

    The indexer:
        - loads the ISAD record and related objects
        - builds a Solr-compatible document with display, facet, search, and sort fields
        - supports indexing via pysolr or direct HTTP requests
        - supports commit and delete operations

    Notes
    -----
    Indexing is performed only when ``isad.published`` is True.
    """

    def __init__(self, isad_id):
        """
        Initializes the catalog indexer for a specific ISAD record.

        Parameters
        ----------
        isad_id : int
            Primary key of the ISAD record to be indexed.
        """
        self.isad_id = isad_id
        self.isad = self._get_isad(isad_id)
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG_NEW", "catalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
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
        Indexes the ISAD record into the catalog Solr core using pysolr.

        Notes
        -----
        This method indexes only if the record is published.
        """
        if self.isad.published:
            self.create_solr_document()
            try:
                self.solr.add([self.doc])
                print("Indexing ISAD(G) %s!" % self.isad.reference_code)
            except pysolr.SolrError as e:
                print('Error with Report No. %s! Error: %s' % (self.isad.reference_code, e))

    def index_with_requests(self):
        """
        Indexes the ISAD record into the catalog Solr core using HTTP requests.

        This method posts the generated document to Solr's JSON update endpoint.
        It is used as an alternative to pysolr.

        Notes
        -----
        This method indexes only if the record is published.
        """
        if self.isad.published:
            self.create_solr_document()
            r = requests.post("%s/update/json/docs" % self.solr_url, json=self.doc, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
            if r.status_code == 200:
                print('Record successfully indexed: %s' % self.isad.reference_code)
            else:
                print('Error with Report No. %s! Error: %s' % (self.isad.reference_code, r.text))

    def commit(self):
        """
        Commits pending Solr index changes for the catalog core.

        Notes
        -----
        This uses an explicit commit request to Solr. Some deployment setups may
        rely on auto-commit; others may require manual commits after batches.
        """
        r = requests.post("%s/update/" % self.solr_url, params={'commit': 'true'}, json={}, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
        print(r.text)

    def delete(self):
        """
        Removes the ISAD record from the catalog Solr core.
        """
        self.solr.delete(id=self._get_solr_id(), commit=True)

    def _get_isad(self, isad_id):
        """
        Retrieves the ISAD record with related objects optimized for indexing.

        Parameters
        ----------
        isad_id : int
            Primary key of the ISAD record.

        Returns
        -------
        isad.models.Isad or None
            The ISAD instance if found, otherwise None.
        """
        qs = Isad.objects.filter(pk=isad_id)
        qs = qs.select_related('archival_unit')
        qs = qs.select_related('original_locale')
        qs = qs.select_related('access_rights')
        qs = qs.select_related('reproduction_rights')
        qs = qs.select_related('rights_restriction_reason')
        try:
            return qs.get()
        except ObjectDoesNotExist:
            return None

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

        The document includes:
            - display fields used by UI rendering
            - facet fields used for filtering/aggregation
            - locale-specific search fields
            - sort fields used for stable ordering
        """
        self.doc['id'] = self._get_solr_id()
        self.doc['ams_id'] = self.isad.archival_unit.id

        # Display field
        self.doc['record_origin'] = "Archives"
        self.doc['primary_type'] = "Archival Unit"
        self.doc['description_level'] = self._get_description_level()
        self.doc['title'] = self.isad.title
        self.doc['reference_code'] = self.isad.reference_code
        self.doc['date_created'] = self._get_date_created_display()
        self.doc['creator'] = self._get_creator()

        # Archival Unit specific display fields
        self.doc['parent_unit'] = self._get_parent_unit()
        self.doc['archival_unit_theme'] = list(map(lambda t: t.theme, self.isad.archival_unit.theme.all()))

        # Facet fields
        self.doc['record_origin_facet'] = "Archives"
        # self.doc['primary_type_facet'] = "Archival Unit"
        self.doc['description_level_facet'] = self._get_description_level()
        self.doc['year_created_facet'] = self._get_date_created_facet()
        self.doc['archival_unit_theme_facet'] = list(map(lambda t: t.theme, self.isad.archival_unit.theme.all()))

        # Search fields
        self.doc["title_search_en"] = self._get_title("en")
        self.doc["title_search_hu"] = self._get_title("hu")
        self.doc["title_search_ru"] = self._get_title("ru")
        self.doc["title_search_pl"] = self._get_title("pl")

        self.doc["contents_summary_search_en"] = self._get_contents_summary_search_values('en')
        self.doc["contents_summary_search_hu"] = self._get_contents_summary_search_values('hu')
        self.doc["contents_summary_search_ru"] = self._get_contents_summary_search_values('ru')
        self.doc["contents_summary_search_pl"] = self._get_contents_summary_search_values('pl')

        # Sort fields
        self.doc["fonds_sort"] = self.isad.archival_unit.fonds
        self.doc["subfonds_sort"] = self.isad.archival_unit.subfonds
        self.doc["series_sort"] = self.isad.archival_unit.series
        self.doc["container_number_sort"] = 0
        self.doc["folder_number_sort"] = 0
        self.doc["sequence_number_sort"] = 0
        self.doc["title_sort"] = self._get_title("en")

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

    def _get_parent_unit(self):
        """
        Returns the title of the parent unit for subfonds and series records.

        Returns
        -------
        str or None
            Fonds title for subfonds records, subfonds title for series records,
            otherwise None.
        """
        if self.isad.description_level == 'SF':
            return self.isad.archival_unit.get_fonds().title_full
        if self.isad.description_level == 'S':
            return self.isad.archival_unit.get_subfonds().title_full
        return None

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
            date = ""
        return date

    def _get_date_created_facet(self):
        """
        Builds the year facet values for the record.

        Returns
        -------
        list
            List of years covered by the record. If a year range exists, all
            years in the range are included.
        """
        date = []

        if self.isad.year_to:
            for year in range(self.isad.year_from, self.isad.year_to + 1):
                date.append(year)
        else:
            date.append(str(self.isad.year_from))

        return date

    def _get_creator(self):
        """
        Returns a list of creators for the ISAD record.

        Combines free-text ISAD creators with the linked ISAAR authority name
        when present.

        Returns
        -------
        list of str
            Creator names.
        """
        creators = list(c.creator for c in self.isad.isadcreator_set.all())
        if self.isad.isaar:
            creators.append(self.isad.isaar.name)
        return creators

    def _get_fonds_name(self):
        """
        Returns the fonds-level title for indexing.

        Returns
        -------
        str
            Fonds title (full form).
        """
        if self.isad.description_level == 'SF' or self.isad.description_level == 'S':
            return self.isad.archival_unit.get_fonds().title_full
        else:
            return self.isad.archival_unit.title_full

    def _get_subfonds_name(self):
        """
        Returns the subfonds label for indexing when applicable.

        Returns
        -------
        str or None
            Subfonds reference code and title when applicable, otherwise None.
        """
        if self.isad.description_level == 'SF' or self.isad.description_level == 'S':
            sf = self.isad.archival_unit.get_subfonds()
            if sf.subfonds != 0:
                return "%s %s" % (sf.reference_code, sf.title)
            else:
                return None
        else:
            return None

    def _get_title(self, locale):
        """
        Returns the title value for a given locale-specific search field.

        Parameters
        ----------
        locale : str
            Locale code (e.g., ``'en'``, ``'hu'``, ``'ru'``, ``'pl'``).

        Returns
        -------
        str or None
            Title for the requested locale, or None if no locale-specific title
            is available.
        """
        if locale == 'en':
            return self.isad.title
        else:
            if self.isad.archival_unit.original_locale_id == locale.upper():
                return getattr(self.isad.archival_unit, "title_original")
            else:
                return None

    def _get_contents_summary_search_values(self, locale):
        """
        Returns a list of text fields used for full-text search for a locale.

        For English, fields are taken from the primary (non-original) values.
        For other locales, fields are taken from the ``*_original`` fields when
        the ISAD record's original locale matches the requested locale.

        Parameters
        ----------
        locale : str
            Locale code (e.g., ``'en'``, ``'hu'``, ``'ru'``, ``'pl'``).

        Returns
        -------
        list of str
            Non-null text values for inclusion in search fields.
        """
        values = []
        if locale == 'en':
            values.append(self.isad.scope_and_content_abstract)
            values.append(self.isad.scope_and_content_narrative)
            values.append(self.isad.administrative_history)
            values.append(self.isad.archival_history)
        else:
            if self.isad.original_locale_id == locale.upper():
                values.append(self.isad.scope_and_content_abstract_original)
                values.append(self.isad.scope_and_content_narrative_original)
                values.append(self.isad.administrative_history_original)
                values.append(self.isad.archival_history_original)
        return list(filter(lambda value: value is not None, values))

    def _remove_duplicates(self):
        """
        Removes duplicate values from list-based Solr fields.
        """
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))

    def _store_json(self):
        """
        Stores the raw JSON representation of the record for debugging or reuse.

        This method is currently a no-op and exists as a placeholder for future
        extensions.
        """
        pass
