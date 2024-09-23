import urllib

import meilisearch
import pysolr
import requests
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

    def get_solr_document(self):
        return self.doc

    def index(self):
        if hasattr(self.finding_aids_entity.archival_unit, 'isad'):
            if self.finding_aids_entity.archival_unit.isad.published:
                self._index_record()
                self._remove_duplicates()
                try:
                    self.meilisearch_index.add_documents([self.doc])
                except Exception as e:
                    print('Error with Report No. %s! Error: %s' % (self.doc['id'], e))
        else:
            print("Finding Aids record doesn't exists. %s!" % self.finding_aids_entity.archival_reference_code)

    def delete(self):
        self.meilisearch_index.delete_document(document_id=self._get_meilisearch_id())

    def _get_finding_aids_record(self, finding_aids_entity_id):
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

    def _index_record(self):
        self.doc['id'] = self._get_meilisearch_id()
        self.doc['ams_id'] = self.finding_aids_entity.id
        self.doc['call_number'] = self.finding_aids_entity.archival_reference_code
        self.doc['guid'] = "osa:%s" % self.finding_aids_entity.uuid

        # Display field
        self.doc['record_origin'] = "Archives"
        self.doc['primary_type'] = self.finding_aids_entity.primary_type.type
        self.doc['description_level'] = self._get_description_level()
        self.doc['container_type'] = self.finding_aids_entity.container.carrier_type.type

        if self.finding_aids_entity.access_rights:
            self.doc['access_rights'] = self.finding_aids_entity.access_rights.statement

        if self.finding_aids_entity.original_locale:
            self.doc['original_locale'] = self.finding_aids_entity.original_locale.id

        # Title
        self.doc['title'] = self.finding_aids_entity.title
        if self.finding_aids_entity.title_original:
            self.doc['title_original'] = self.finding_aids_entity.title_original

        # Contents Summary
        self.doc['contents_summary'] = strip_tags(self.finding_aids_entity.contents_summary)
        if self.finding_aids_entity.contents_summary_original:
            self.doc['contents_summary_original'] = strip_tags(self.finding_aids_entity.contents_summary_original)

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

        # Container Number
        self.doc['container_type'] = self.finding_aids_entity.container.carrier_type.type
        self.doc['container_number'] = self.finding_aids_entity.container.container_no
        self.doc['folder_number'] = self.finding_aids_entity.folder_no
        self.doc['sequence_number'] = self.finding_aids_entity.sequence_no

        # Facets
        self.doc['subject'] = self._get_subjects(wikidata=True)
        # self.doc['subject_wikidata'] = self._get_subjects(wikidata=True)
        self.doc['contributor'] = self._get_contributors(wikidata=True)
        # self.doc['contributor_wikidata'] = self._get_contributors(wikidata=True)
        self.doc['geo'] = self._get_geo(wikidata=True)
        # self.doc['geo_wikidata'] = self._get_geo(wikidata=True)
        self.doc['keyword'] = self._get_keywords()
        self.doc['year_created'] = self._get_date_created_facet()
        self.doc['language'] = self._get_languages(wikidata=True)
        # self.doc['language_wikidata'] = self._get_languages(wikidata=True)
        self.doc['availability'] = self._get_availability()
        self.doc['series_facet'] = "%s - %s#%s" % (
            self.finding_aids_entity.archival_unit.reference_code,
            self.finding_aids_entity.archival_unit.title,
            self.finding_aids_entity.archival_unit.id
        )

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

    def _get_date_created_display(self):
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
        return self.finding_aids_entity.archival_unit.title_full

    def _get_info(self):
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
        return self.finding_aids_entity.archival_unit.id

    def _get_digital_version_info(self):
        did_generator = DigitalVersionIdentifierGenerator(self.finding_aids_entity)
        val = {
            'digital_version_exists': did_generator.detect(),
            'digital_version_online': did_generator.detect_available_online(),
            'digital_version_barcode': did_generator.generate_identifier()
        }
        return val

    def _get_digital_collection(self):
        digital_version = DigitalVersion.objects.filter(finding_aids_entity=self.finding_aids_entity)\
            .values('digital_collection').first()
        if 'digital_collection' in digital_version:
            return digital_version['digital_collection']
        else:
            return self.finding_aids_entity.archival_unit.get_fonds().title

    def _get_value_with_wikidata_id(self, obj):
        wikidata_id = getattr(obj, "wikidata_id")
        if wikidata_id:
            return "%s#%s" % (str(obj), wikidata_id)
        else:
            return str(obj)

    def _get_subjects(self, wikidata=False):
        subjects = []
        # Subject people
        for person in self.finding_aids_entity.subject_person.all():
            if wikidata:
                subjects.append(self._get_value_with_wikidata_id(person))
            else:
                subjects.append(person)

        # Subject corporation
        for corporation in self.finding_aids_entity.subject_corporation.all():
            if wikidata:
                subjects.append(self._get_value_with_wikidata_id(corporation))
            else:
                subjects.append(corporation)

        return subjects

    def _get_keywords(self):
        keywords = []
        # Subjects
        for fa_subject in self.finding_aids_entity.findingaidsentitysubject_set.all():
            keywords.append(fa_subject.subject)

        # Subject keywords
        for keyword in self.finding_aids_entity.subject_keyword.all():
            keywords.append(str(keyword))
        return keywords

    def _get_duration(self):
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
        languages = []
        for fa_language in self.finding_aids_entity.findingaidsentitylanguage_set.all():
            if wikidata:
                languages.append(self._get_value_with_wikidata_id(fa_language.language))
            else:
                languages.append(str(fa_language.language))
        return languages


    def _get_date_created_facet(self):
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
        digital_version = self._get_digital_version_info()
        if digital_version['digital_version_exists'] and not digital_version['digital_version_online']:
            return 'Digitally Anywhere / With Registration'

        if digital_version['digital_version_exists'] and digital_version['digital_version_online']:
            return 'Digitally Anywhere / Without Registration'

        return 'In the Research Room'

    def _get_identifiers(self):
        digital_version = self._get_digital_version_info()
        if digital_version['digital_version_exists']:
            return digital_version['digital_version_barcode']

    def _get_search_field(self, ams_field, solr_field):
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