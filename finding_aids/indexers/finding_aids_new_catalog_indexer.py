import pysolr
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from hashids import Hashids
from langdetect import detect

from finding_aids.models import FindingAidsEntity


class FindingAidsNewCatalogIndexer:
    """
    Class to index Finding Aids records to Solr for the catalog.
    """

    def __init__(self, finding_aids_entity_id):
        self.finding_aids_entity_id = finding_aids_entity_id
        self.finding_aids_entity = self._get_finding_aids_record(finding_aids_entity_id)
        self.hashids = Hashids(salt="osacontent", min_length=10)
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG_NEW", "catalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, always_commit=True)
        self.locales = ['en', 'hu', 'ru', 'pl']
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
        self.solr.delete(id=self._get_solr_id(), commit=True)

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
        try:
            return qs.get()
        except ObjectDoesNotExist:
            return None

    def create_solr_document(self):
        self._index_record()
        self._store_json()
        self._remove_duplicates()

    def _index_record(self):
        self.doc['id'] = self._get_solr_id()
        self.doc['ams_id'] = self.finding_aids_entity.id

        # Display field
        self.doc['record_origin'] = "Archives"
        self.doc['primary_type'] = self.finding_aids_entity.primary_type.type
        self.doc['description_level'] = self._get_description_level()
        self.doc['title'] = self.finding_aids_entity.title
        self.doc['reference_code'] = self.finding_aids_entity.archival_reference_code
        self.doc['date_created'] = self._get_date_created_display()

        # Digital Version related fields
        self.doc['digital_version_exists'] = self._get_digital_version_info()['digital_version_exists']
        self.doc['digital_version_online'] = self._get_digital_version_info()['digital_version_online']
        self.doc['digital_version_barcode'] = self._get_digital_version_info()['digital_version_barcode']

        # Archival Unit Specific fields
        self.doc['fonds_name'] = self.finding_aids_entity.archival_unit.get_fonds().title_full
        self.doc['subfonds_name'] = "%s %s" % (
            self.finding_aids_entity.archival_unit.get_subfonds().reference_code,
            self.finding_aids_entity.archival_unit.get_subfonds().title)
        self.doc['series_name'] = "%s %s" % (
            self.finding_aids_entity.archival_unit.reference_code,
            self.finding_aids_entity.archival_unit.title)
        self.doc['archival_unit_theme'] = list(map(lambda t: t.theme, self.finding_aids_entity.archival_unit.theme.all()))

        # Facet fields
        self.doc['record_origin_facet'] = "Archives"
        self.doc['primary_type_facet'] = self.finding_aids_entity.primary_type.type
        self.doc['description_level_facet'] = self._get_description_level()
        self.doc['subject_facet'] = self._get_subjects()
        self.doc['contributor_facet'] = self._get_contributors()
        self.doc['geo_facet'] = self._get_geo()
        self.doc['year_created_facet'] = self._get_date_created_facet()
        self.doc['language_facet'] = list(
            map(lambda l: str(l.language), self.finding_aids_entity.findingaidsentitylanguage_set.all())
        )
        self.doc['availability_facet'] = self._get_availability()

        # Search fields
        self.doc['identifier_search'] = self._get_identifiers()
        self._get_search_field('title', 'title_search')
        self._get_search_field('contents_summary', 'contents_summary_search')


    def _get_solr_id(self):
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
                return "%s - %s" % (self.finding_aids_entity.date_from, self.finding_aids_entity.date_to)
        return str(self.finding_aids_entity.date_from)

    def _get_digital_version_info(self):
        val = {
            'digital_version_exists': False,
            'digital_version_online': False,
            'digital_version_barcode': ''
        }
        if self.finding_aids_entity.digital_version_exists:
            val['digital_version_exists'] = True
            val['digital_version_online'] = self.finding_aids_entity.digital_version_online
            barcode = self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_")
            val['digital_version_barcode'] = barcode
        else:
            if self.finding_aids_entity.container.digital_version_exists:
                val['digital_version_exists'] = True
                val['digital_version_online'] = self.finding_aids_entity.container.digital_version_online
                if self.finding_aids_entity.container.barcode:
                    val['digital_version_barcode'] = self.finding_aids_entity.container.barcode

        return val

    def _get_subjects(self, wikidata=False):
        subjects = []
        # Subjects
        for fa_subject in self.finding_aids_entity.findingaidsentitysubject_set.all():
            subjects.append(fa_subject.subject)

        # Subject people
        for person in self.finding_aids_entity.subject_person.all():
            subjects.append(str(person))

        # Subject corporation
        for corporation in self.finding_aids_entity.subject_corporation.all():
            subjects.append(str(corporation))

        # Subject headings
        for heading in self.finding_aids_entity.subject_heading.all():
            subjects.append(heading.subject)

        # Subject keywords
        for keyword in self.finding_aids_entity.subject_keyword.all():
            subjects.append(keyword.keyword)

        return subjects

    def _get_contributors(self):
        contributors = []

        # Associated person
        for ap in self.finding_aids_entity.findingaidsentityassociatedperson_set.all():
            contributors.append(str(ap.associated_person))

        # Associated corporation
        for ac in self.finding_aids_entity.findingaidsentityassociatedcorporation_set.all():
            contributors.append(str(ac.associated_corporation))

        return contributors

    def _get_geo(self):
        geo = []

        # Spatial coverage country
        for country in self.finding_aids_entity.spatial_coverage_country.all():
            geo.append(str(country))

        # Spatial coverage place
        for place in self.finding_aids_entity.spatial_coverage_place.all():
            geo.append(str(place))

        # Associated country
        for ac in self.finding_aids_entity.findingaidsentityassociatedcountry_set.all():
            geo.append(str(ac.associated_country))

        # Associated place
        for ap in self.finding_aids_entity.findingaidsentityassociatedplace_set.all():
            geo.append(str(ap.associated_place))

        return geo

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
            locale = self.finding_aids_entity.original_locale.locale.lower()
            self.doc['%s_en' % solr_field] = getattr(self.finding_aids_entity, ams_field)
            self.doc['%s_%s' % (solr_field, locale)] = getattr(self.finding_aids_entity, "%s_original" % ams_field)
        else:
            locale = detect(self.finding_aids_entity.title)
            if locale in self.locales:
                self.doc['%s_%s' % (solr_field, locale)] = getattr(self.finding_aids_entity, ams_field)
            else:
                self.doc['%s_general' % solr_field] = getattr(self.finding_aids_entity, ams_field)

    def _remove_duplicates(self):
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))

    def _store_json(self):
        pass