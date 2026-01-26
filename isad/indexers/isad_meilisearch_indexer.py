import re

import meilisearch
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import strip_tags
from hashids import Hashids

from isad.models import Isad


class ISADMeilisearchIndexer:
    """
    Indexer for publishing ISAD(G) records to Meilisearch for the catalog.

    This indexer transforms an :class:`isad.models.Isad` instance into a
    Meilisearch document and supports indexing and deletion operations.

    The indexer:
        - loads the ISAD record and related objects
        - builds a Meilisearch-compatible document (display fields and search text)
        - removes duplicate list values
        - adds or deletes documents in the configured Meilisearch index

    Notes
    -----
    Indexing is performed only when ``isad.published`` is True.
    """

    def __init__(self, isad_id):
        """
        Initializes the Meilisearch indexer for a specific ISAD record.

        Parameters
        ----------
        isad_id : int
            Primary key of the ISAD record to be indexed.
        """
        self.isad_id = isad_id
        self.isad = self._get_isad(isad_id)

        self.meilisearch_url = getattr(settings, "MEILISEARCH_URL", "")
        self.meilisearch_api_key = getattr(settings, "MEILISEARCH_API_KEY", "")
        self.meilisearch_index = getattr(settings, "MEILISEARCH_INDEX", "meilisearch")

        self.client = meilisearch.Client(self.meilisearch_url, self.meilisearch_api_key)
        self.meilisearch_index = self.client.index(self.meilisearch_index)
        self.doc = {}

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

    def index(self):
        """
        Indexes the ISAD record into Meilisearch.

        Notes
        -----
        This method indexes only if the record is published.
        """
        if self.isad.published:
            self._index_record()
            self._remove_duplicates()
            self.meilisearch_index.add_documents([self.doc])

    def delete(self):
        """
        Removes the ISAD record from Meilisearch.
        """
        self.meilisearch_index.delete_document(self._get_meilisearch_id())

    def _index_record(self):
        """
        Populates Meilisearch fields derived from the ISAD record.

        The document includes display fields (title, dates, creator, etc.) and
        concatenated text fields used for full-text search.
        """
        self.doc['id'] = self._get_meilisearch_id()
        self.doc['ams_id'] = self.isad.archival_unit.id
        self.doc['call_number'] = self.isad.reference_code

        # Display field
        self.doc['title'] = self.isad.title
        self.doc['record_origin'] = "Archives"
        self.doc['primary_type'] = "Archival Unit"
        self.doc['description_level'] = self._get_description_level()
        self.doc['date_created'] = self._get_date_created_display()
        self.doc['year_created'] = self._get_date_created_facet()
        self.doc['creator'] = self._get_creator()
        self.doc['parent_unit'] = self._get_parent_unit()
        self.doc['archival_unit_theme'] = list(map(lambda t: t.theme, self.isad.archival_unit.theme.all()))

        # Title fields
        if self.isad.archival_unit.title_original:
            self.doc['title_original'] = self.isad.archival_unit.title_original

        # Contents summary
        self.doc["contents_summary"] = self._get_contents_summary_search_values('en')
        if self.isad.original_locale:
            self.doc["contents_summary_original"] = self._get_contents_summary_search_values(self.isad.original_locale.id)

    def _get_meilisearch_id(self):
        """
        Computes the Meilisearch document identifier.

        The identifier is a Hashids-encoded value derived from the fonds,
        subfonds, and series numbers of the archival unit.

        Returns
        -------
        str
            Stable Meilisearch document identifier.
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

    def _get_contents_summary_search_values(self, locale):
        """
        Returns a list of text fields used for full-text search for a locale.

        For English, values are taken from the primary text fields and stripped
        of HTML tags. For other locales, values are taken from the
        ``*_original`` fields when the ISAD record's original locale matches the
        requested locale.

        Parameters
        ----------
        locale : str
            Locale code (e.g., ``'en'`` or ``'HU'`` style IDs, depending on usage).

        Returns
        -------
        list of str
            Non-empty text values for inclusion in Meilisearch fields.
        """
        values = []
        if locale == 'en':
            if self.isad.scope_and_content_abstract:
                values.append(strip_tags(self.isad.scope_and_content_abstract))

            if self.isad.scope_and_content_narrative:
                values.append(strip_tags(self.isad.scope_and_content_narrative))

            if self.isad.administrative_history:
                values.append(strip_tags(self.isad.administrative_history))

            if self.isad.archival_history:
                values.append(strip_tags(self.isad.archival_history))
        else:
            if self.isad.original_locale_id == locale.upper():
                if self.isad.scope_and_content_abstract_original:
                    values.append(self.isad.scope_and_content_abstract_original)

                if self.isad.scope_and_content_narrative_original:
                    values.append(self.isad.scope_and_content_narrative_original)

                if self.isad.administrative_history_original:
                    values.append(self.isad.administrative_history_original)

                if self.isad.archival_history_original:
                    values.append(self.isad.archival_history_original)
        return list(filter(lambda v: v and len(v) > 0, values))

    def _remove_duplicates(self):
        """
        Removes duplicate values from list-based Meilisearch fields.
        """
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))
