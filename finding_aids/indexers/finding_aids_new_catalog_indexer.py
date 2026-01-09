import urllib

import pysolr
import requests
from django.conf import settings
from hashids import Hashids
from langdetect import detect, LangDetectException
from requests.auth import HTTPBasicAuth

from digitization.models import DigitalVersion
from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator
from finding_aids.models import FindingAidsEntity


class FindingAidsNewCatalogIndexer:
    """
    Indexes Finding Aids entities into the Solr "catalog" core.

    Responsibilities:
        - fetch a fully-related FindingAidsEntity record efficiently
        - build a Solr document with:
            - display fields
            - facet fields
            - search fields (multilingual aware)
            - sort fields
        - enforce publication gating (only index if parent ISAD is published)
        - enforce confidentiality rules (redact sensitive fields when confidential)
        - enrich some records with external technical metadata

    The resulting Solr document is stored in `self.doc`.
    """

    def __init__(self, finding_aids_entity_id):
        """
        Initializes the indexer and prepares Solr connectivity.

        Args:
            finding_aids_entity_id: Primary key of the FindingAidsEntity to index.

        Side effects:
            - loads the FindingAidsEntity with related objects needed for indexing
            - prepares a pysolr client using SOLR_URL and SOLR_CORE_CATALOG_NEW settings
        """
        self.finding_aids_entity_id = finding_aids_entity_id
        self.finding_aids_entity = self._get_finding_aids_record(finding_aids_entity_id)
        self.hashids = Hashids(salt="osacontent", min_length=10)
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG_NEW", "catalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
        self.locales = ['en', 'hu', 'ru', 'pl']
        self.doc = {}

    def get_solr_document(self):
        """
        Returns the currently built Solr document dictionary.
        """
        return self.doc

    def index(self):
        """
        Indexes the record into Solr using pysolr.

        Indexing is guarded by publication rules:
            - the archival unit must have an ISAD record
            - the ISAD record must be published

        When allowed:
            - builds the Solr document
            - adds it to Solr (without committing)
        """
        if hasattr(self.finding_aids_entity.archival_unit, 'isad'):
            if self.finding_aids_entity.archival_unit.isad.published:
                self.create_solr_document()
                try:
                    self.solr.add([self.doc])
                except pysolr.SolrError as e:
                    print('Error with Report No. %s! Error: %s' % (self.doc['id'], e))
        else:
            print("Finding Aids record doesn't exists. %s!" % self.finding_aids_entity.archival_reference_code)

    def index_with_requests(self):
        """
        Indexes the record into Solr using the requests API endpoint.

        This is an alternative to pysolr.add(), and uses:
            POST <solr_url>/update/json/docs/

        Indexing is guarded by the same publication rules as `index()`.
        """
        if hasattr(self.finding_aids_entity.archival_unit, 'isad'):
            if self.finding_aids_entity.archival_unit.isad.published:
                self.create_solr_document()
                r = requests.post("%s/update/json/docs/" % self.solr_url, json=self.doc, auth=HTTPBasicAuth(
                    getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
                ))
                if r.status_code == 200:
                    print('Record successfully indexed: %s' % self.finding_aids_entity.archival_reference_code)
                else:
                    print('Error with indexing %s: %s' % (self.finding_aids_entity.archival_reference_code, r.text))

    def commit(self):
        """
        Sends a commit request to Solr.

        This is typically called after one or more `index()` calls to
        make the updates visible.
        """
        r = requests.post("%s/update/" % self.solr_url, params={'commit': 'true'}, json={}, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
        print(r.text)

    def delete(self):
        """
        Deletes the record from Solr by its Solr id and commits immediately.
        """
        self.solr.delete(id=self._get_solr_id(), commit=True)

    def _get_finding_aids_record(self, finding_aids_entity_id):
        """
        Loads a FindingAidsEntity with related objects needed for indexing.

        Uses select_related/prefetch_related to reduce query count when building
        facets and search fields.
        """
        qs = FindingAidsEntity.objects.filter(pk=finding_aids_entity_id)
        qs = qs.select_related('archival_unit')
        qs = qs.select_related('container')
        qs = qs.select_related('original_locale')
        qs = qs.select_related('primary_type')
        qs = qs.prefetch_related('genre')
        qs = qs.prefetch_related('spatial_coverage_country')
        qs = qs.prefetch_related('spatial_coverage_place')
        qs = qs.prefetch_related('subject_person')
        qs = qs.prefetch_related('subject_corporation')
        qs = qs.prefetch_related('subject_heading')
        qs = qs.prefetch_related('subject_keyword')
        return qs.get()

    def create_solr_document(self):
        """
        Builds the Solr document for the current record.

        Steps:
            1. Populate document fields
            2. Remove duplicates in list-valued fields
        """
        self._index_record()
        self._remove_duplicates()

    def _index_record(self):
        """
        Populates `self.doc` with all Solr fields for the record.

        This method handles:
            - id, guid, and reference codes
            - confidentiality redaction of sensitive fields
            - digital version fields and technical metadata enrichment
            - facets and search fields (including language-aware fields)
            - sort fields used by the Solr UI/query layer
        """
        self.doc['id'] = self._get_solr_id()
        self.doc['ams_id'] = self.finding_aids_entity.id
        self.doc['call_number'] = self.finding_aids_entity.archival_reference_code
        self.doc['guid'] = "osa:%s" % self.finding_aids_entity.uuid

        # Display field
        self.doc['record_origin'] = "Archives"
        self.doc['primary_type'] = self.finding_aids_entity.primary_type.type
        self.doc['description_level'] = self._get_description_level()
        self.doc['container_type'] = self.finding_aids_entity.container.carrier_type.type

        # Access Rights Confidential
        if self.finding_aids_entity.confidential:
            self.doc['access_rights'] = 'Confidential'
        else:
            if self.finding_aids_entity.access_rights:
                self.doc['access_rights'] = self.finding_aids_entity.access_rights.statement

        # Original Locale
        if self.finding_aids_entity.original_locale:
            self.doc['original_locale'] = self.finding_aids_entity.original_locale.id

        # Confidential
        if self.finding_aids_entity.confidential:
            if self.finding_aids_entity.confidential_display_text:
                self.doc['title'] = self.finding_aids_entity.confidential_display_text
            else:
                self.doc['title'] = "The metadata of this document contains sensitive information."

        # Normal fields
        else:
            self.doc['title'] = self.finding_aids_entity.title
            self.doc['title_original'] = self.finding_aids_entity.title_original
            self.doc['contents_summary'] = self.finding_aids_entity.contents_summary
            self.doc['contents_summary_original'] = self.finding_aids_entity.contents_summary_original
            self.doc['reference_code'] = self.finding_aids_entity.archival_reference_code
            self.doc['date_created'] = self._get_date_created_display()
            self.doc['info'] = self._get_info()

        # Digital Version related fields
        digital_version_info = self._get_digital_version_info()
        self.doc['digital_version_exists'] = digital_version_info['digital_version_exists']
        self.doc['digital_version_online'] = digital_version_info['digital_version_online']
        self.doc['digital_version_barcode'] = digital_version_info['digital_version_barcode']
        self.doc['digital_version_technical_metadata'] = self._get_digital_version_technical_metadata()

        if digital_version_info['digital_version_online']:
            self.doc['digital_collection_facet'] = self._get_digital_collection()

        # Archival Unit Specific fields
        self.doc['parent_unit'] = self._get_parent_unit()
        self.doc['archival_unit_theme'] = list(map(lambda t: t.theme, self.finding_aids_entity.archival_unit.theme.all()))

        # Finding Aids filter id
        self.doc['fonds_id'] = self.finding_aids_entity.archival_unit.get_fonds().id
        self.doc['subfonds_id'] = self.finding_aids_entity.archival_unit.get_subfonds().id
        self.doc['series_id'] = self.finding_aids_entity.archival_unit.id

        # Facet fields
        if not self.finding_aids_entity.confidential:
            self.doc['record_origin_facet'] = "Archives"
            self.doc['primary_type_facet'] = self.finding_aids_entity.primary_type.type
            self.doc['description_level_facet'] = self._get_description_level()
            self.doc['subject_facet'] = self._get_subjects()
            self.doc['subject_wikidata_facet'] = self._get_subjects(wikidata=True)
            self.doc['contributor_facet'] = self._get_contributors()
            self.doc['contributor_wikidata_facet'] = self._get_contributors(wikidata=True)
            self.doc['geo_facet'] = self._get_geo()
            self.doc['geo_wikidata_facet'] = self._get_geo(wikidata=True)
            self.doc['keyword_facet'] = self._get_keywords()
            self.doc['year_created_facet'] = self._get_date_created_facet()
            self.doc['language_facet'] = self._get_languages()
            self.doc['language_wikidata_facet'] = self._get_languages(wikidata=True)
            self.doc['availability_facet'] = self._get_availability()
            self.doc['series_facet'] = "%s - %s" % (
                self.finding_aids_entity.archival_unit.reference_code,
                self.finding_aids_entity.archival_unit.title,
            )

        # Search fields
        if not self.finding_aids_entity.confidential:
            self.doc['identifier_search'] = self._get_identifiers()
            self._get_search_field('title', 'title_search')
            self._get_search_field('contents_summary', 'contents_summary_search')
            self.doc['subject_search'] = self._get_subjects()
            self.doc['contributor_search'] = self._get_contributors()
            self.doc['geo_search'] = self._get_geo()
            self.doc['keyword_search'] = self._get_keywords()

        # Sort fields
        self.doc["fonds_sort"] = self.finding_aids_entity.archival_unit.fonds
        self.doc["subfonds_sort"] = self.finding_aids_entity.archival_unit.subfonds
        self.doc["series_sort"] = self.finding_aids_entity.archival_unit.series
        self.doc["container_number_sort"] = self.finding_aids_entity.container.container_no
        self.doc["folder_number_sort"] = self.finding_aids_entity.folder_no
        self.doc["sequence_number_sort"] = self.finding_aids_entity.sequence_no
        self.doc["title_sort"] = self.finding_aids_entity.title

    def _get_solr_id(self):
        """
        Returns the Solr document id.

        Preference order:
            1. catalog_id (stored on the entity)
            2. hashids-encoded primary key
        """
        if self.finding_aids_entity.catalog_id:
            return self.finding_aids_entity.catalog_id
        else:
            return self.hashids.encode(self.finding_aids_entity.id)

    def _get_description_level(self):
        """
        Converts the entity level code to a display label for Solr.
        """
        if self.finding_aids_entity.level == 'F':
            return 'Folder'
        else:
            return 'Item'

    def _get_date_created_display(self):
        """
        Produces a human-readable date string for display.

        Supports:
            - single dates
            - date ranges (from/to)
            - approximate date spans ("ca.") when date_ca_span is non-zero
        """
        if self.finding_aids_entity.date_to:
            if self.finding_aids_entity.date_from != self.finding_aids_entity.date_to:
                if self.finding_aids_entity.date_ca_span != 0:
                    return "ca. %s - %s" % (self.finding_aids_entity.date_from, self.finding_aids_entity.date_to)
                else:
                    return "%s - %s" % (self.finding_aids_entity.date_from, self.finding_aids_entity.date_to)

        if self.finding_aids_entity.date_ca_span != 0:
            return "ca. %s" % str(self.finding_aids_entity.date_from)
        else:
            return str(self.finding_aids_entity.date_from)

    def _get_parent_unit(self):
        """
        Returns the parent archival unit title for display.
        """
        return self.finding_aids_entity.archival_unit.title_full

    def _get_info(self):
        """
        Builds a compact info string for display.

        Aggregates:
            - genre terms
            - language values (with usage when available)
            - explicit typed dates
            - fallback to main date_from/date_to when no typed dates exist
            - duration (human-readable)
        """
        values = []

        # Genre
        for genre in self.finding_aids_entity.genre.all():
            values.append(genre.genre)

        # Languages
        for language in self.finding_aids_entity.findingaidsentitylanguage_set.all():
            if language.language_usage:
                values.append("%s (%s)" % (str(language.language), language.language_usage))
            else:
                values.append(str(language.language))

        # Date
        for date in self.finding_aids_entity.findingaidsentitydate_set.all():
            if date.date_type.type:
                values.append("%s: %s" % (str(date.date_type), str(date.date_from)))
            else:
                values.append(str(date.date))

        # Date
        if self.finding_aids_entity.findingaidsentitydate_set.count() == 0:
            if self.finding_aids_entity.date_to:
                values.append("%s - %s" % (str(self.finding_aids_entity.date_from), str(self.finding_aids_entity.date_to)))
            else:
                values.append(str(self.finding_aids_entity.date_from))

        # Duration
        if self.finding_aids_entity.duration:
            values.append(self._get_duration())

        return ', '.join(values)

    def _get_series_id(self):
        """
        Returns the archival unit id used as a series identifier in Solr.
        """
        return self.finding_aids_entity.archival_unit.id

    def _get_digital_version_info(self):
        """
        Collects digital-version availability and identifier information.

        Uses DigitalVersionIdentifierGenerator to determine:
            - whether a digital version exists
            - whether it is available online
            - the identifier/barcode used in the catalog UI
        """
        did_generator = DigitalVersionIdentifierGenerator(self.finding_aids_entity)
        val = {
            'digital_version_exists': did_generator.detect(),
            'digital_version_online': did_generator.detect_available_online(),
            'digital_version_barcode': did_generator.generate_identifier()
        }
        return val

    def _get_digital_collection(self):
        """
        Determines the digital collection facet value.

        Uses the first related DigitalVersion.digital_collection if available,
        otherwise falls back to the fonds title.
        """
        digital_version = DigitalVersion.objects.filter(finding_aids_entity=self.finding_aids_entity)\
            .values('digital_collection').first()
        if 'digital_collection' in digital_version:
            return digital_version['digital_collection']
        else:
            return self.finding_aids_entity.archival_unit.get_fonds().title

    def _get_value_with_wikidata_id(self, obj):
        """
        Formats an authority value including a Wikidata id when present.

        Output format:
            "<label>#<wikidata_id>" or "<label>"
        """
        wikipedia_id = getattr(obj, "wikidata_id")
        if wikipedia_id:
            return "%s#%s" % (str(obj), wikipedia_id)
        else:
            return str(obj)

    def _get_subjects(self, wikidata=False):
        """
        Returns subject values for facets/search.

        Includes:
            - subject people
            - subject corporations

        When wikidata=True, values are emitted as "<label>#<wikidata_id>" when available.
        """
        subjects = []
        # Subject people
        for person in self.finding_aids_entity.subject_person.all():
            if wikidata:
                subjects.append(self._get_value_with_wikidata_id(person))
            else:
                subjects.append(str(person))

        # Subject corporation
        for corporation in self.finding_aids_entity.subject_corporation.all():
            if wikidata:
                subjects.append(self._get_value_with_wikidata_id(corporation))
            else:
                subjects.append(str(corporation))

        return subjects

    def _get_keywords(self):
        """
        Returns keyword values for facets/search.

        Includes:
            - free-text subjects (FindingAidsEntitySubject)
            - controlled keywords (controlled_list.Keyword)
        """
        keywords = []
        # Subjects
        for fa_subject in self.finding_aids_entity.findingaidsentitysubject_set.all():
            keywords.append(fa_subject.subject)

        # Subject keywords
        for keyword in self.finding_aids_entity.subject_keyword.all():
            keywords.append(str(keyword))
        return keywords

    def _get_duration(self):
        """
        Returns a human-readable duration string derived from entity.duration.
        """
        duration_string = []
        if self.finding_aids_entity.duration:
            hours, remainder = divmod(self.finding_aids_entity.duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours == 1:
                duration_string.append("%s hour" % hours)

            if hours > 1:
                duration_string.append("%s hours" % hours)

            if minutes > 0:
                duration_string.append("%s min." % minutes)
            if seconds > 0:
                duration_string.append("%s sec." % seconds)
        return ' '.join(duration_string)

    def _get_contributors(self, wikidata=False):
        """
        Returns contributor values for facets/search.

        Contributors are derived from associated people and corporations.
        When wikidata=True, emits values as "<label>#<wikidata_id>" when available.
        """
        contributors = []

        # Associated person
        for ap in self.finding_aids_entity.findingaidsentityassociatedperson_set.all():
            if wikidata:
                contributors.append(self._get_value_with_wikidata_id(ap.associated_person))
            else:
                contributors.append(str(ap.associated_person))

        # Associated corporation
        for ac in self.finding_aids_entity.findingaidsentityassociatedcorporation_set.all():
            if wikidata:
                contributors.append(self._get_value_with_wikidata_id(ac.associated_corporation))
            else:
                contributors.append(str(ac.associated_corporation))
        return contributors

    def _get_geo(self, wikidata=False):
        """
        Returns geographic values for facets/search.

        Includes:
            - spatial coverage countries
            - spatial coverage places

        When wikidata=True, emits values as "<label>#<wikidata_id>" when available.
        """
        geo = []

        # Spatial coverage country
        for country in self.finding_aids_entity.spatial_coverage_country.all():
            if wikidata:
                geo.append(self._get_value_with_wikidata_id(country))
            else:
                geo.append(str(country))

        # Spatial coverage place
        for place in self.finding_aids_entity.spatial_coverage_place.all():
            if wikidata:
                geo.append(self._get_value_with_wikidata_id(place))
            else:
                geo.append(str(place))
        return geo

    def _get_languages(self, wikidata=False):
        """
        Returns language values for facets/search.

        Languages come from FindingAidsEntityLanguage links. When wikidata=True,
        the linked language authority may include wikidata ids.
        """
        languages = []
        for fa_language in self.finding_aids_entity.findingaidsentitylanguage_set.all():
            if wikidata:
                languages.append(self._get_value_with_wikidata_id(fa_language.language))
            else:
                languages.append(str(fa_language.language))
        return languages

    def _get_date_created_facet(self):
        """
        Returns year facet values based on date_from/date_to.

        If a date range is present, all years in the inclusive range are emitted.
        """
        date = []
        if len(self.finding_aids_entity.date_from) == 0:
            return None
        else:
            year_from = self.finding_aids_entity.date_from.year
            if self.finding_aids_entity.date_to:
                year_to = self.finding_aids_entity.date_to.year
            else:
                year_to = None

            if year_from > 0:
                if year_to:
                    for year in range(year_from, year_to + 1):
                        date.append(year)
                else:
                    date.append(str(year_from))

            return date

    def _get_availability(self):
        """
        Returns the availability facet value based on digital version status.
        """
        digital_version = self._get_digital_version_info()
        if digital_version['digital_version_exists'] and not digital_version['digital_version_online']:
            return 'Digitally Anywhere / With Registration'

        if digital_version['digital_version_exists'] and digital_version['digital_version_online']:
            return 'Digitally Anywhere / Without Registration'

        return 'In the Research Room'

    def _get_identifiers(self):
        """
        Returns identifier values for identifier_search.

        When a digital version exists, this returns the digital version identifier.
        """
        digital_version = self._get_digital_version_info()
        if digital_version['digital_version_exists']:
            return digital_version['digital_version_barcode']

    def _get_search_field(self, ams_field, solr_field):
        """
        Populates localized search fields in Solr.

        If an original locale is set:
            - writes the English field from the base attribute
            - writes the locale-specific field from the *_original attribute

        If no original locale is set:
            - attempts language detection (langdetect.detect)
            - writes into <solr_field>_<locale> when locale is supported
            - falls back to <solr_field>_general on detection failure/unsupported locale
        """
        if self.finding_aids_entity.original_locale:
            locale = self.finding_aids_entity.original_locale.id.lower()
            self.doc['%s_en' % solr_field] = getattr(self.finding_aids_entity, ams_field)
            self.doc['%s_%s' % (solr_field, locale)] = getattr(self.finding_aids_entity, "%s_original" % ams_field)
        else:
            try:
                locale = detect(self.finding_aids_entity.title)
                if locale in self.locales:
                    self.doc['%s_%s' % (solr_field, locale)] = getattr(self.finding_aids_entity, ams_field)
                else:
                    self.doc['%s_general' % solr_field] = getattr(self.finding_aids_entity, ams_field)
            except LangDetectException:
                self.doc['%s_general' % solr_field] = getattr(self.finding_aids_entity, ams_field)

    def _get_digital_version_technical_metadata(self):
        """
        Fetches technical metadata for still images via IIIF.

        For primary type "Still Image", this:
            - constructs an IIIF image id from archival and container/folder identifiers
            - requests <BASE_IMAGE_URI>/<image_id>/info.json
            - returns the JSON response text when available

        Returns:
            - str containing info.json when successful
            - None when not available or request fails
        """
        if self.finding_aids_entity.primary_type.type == 'Still Image':
            iiif_url = (getattr(settings, 'BASE_IMAGE_URI', 'http://127.0.0.1:8182/iiif/2/'))
            archival_unit_ref_code = self.finding_aids_entity.archival_unit.reference_code\
                .replace(" ", "_")\
                .replace("-", "_")
            item_reference_code = "%s_%04d_%04d" % (
                archival_unit_ref_code,
                self.finding_aids_entity.container.container_no,
                self.finding_aids_entity.folder_no
            )
            image_id = 'catalog/%s/%s.jpg' % (archival_unit_ref_code, item_reference_code)
            image_id = urllib.parse.quote_plus(image_id)
            r = requests.get("%s%s/info.json" % (iiif_url, image_id))

            if r.status_code == 200:
                return r.text
            else:
                return None

    def _remove_duplicates(self):
        """
        Deduplicates list-valued fields in the Solr document.

        Solr facets/search fields can be populated from multiple sources;
        this ensures lists contain unique values only.
        """
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))
