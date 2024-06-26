import pysolr
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from hashids import Hashids
from requests.auth import HTTPBasicAuth

from isad.models import Isad


class ISADNewCatalogIndexer:
    """
    Class to index ISAD(G) records to Solr for the catalog.
    """

    def __init__(self, isad_id):
        self.isad_id = isad_id
        self.isad = self._get_isad(isad_id)
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG_NEW", "catalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
        self.doc = {}

    def get_solr_document(self):
        return self.doc

    def index(self):
        if self.isad.published:
            self.create_solr_document()
            try:
                self.solr.add([self.doc])
                print("Indexing ISAD(G) %s!" % self.isad.reference_code)
            except pysolr.SolrError as e:
                print('Error with Report No. %s! Error: %s' % (self.isad.reference_code, e))

    def index_with_requests(self):
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
        r = requests.post("%s/update/" % self.solr_url, params={'commit': 'true'}, json={}, auth=HTTPBasicAuth(
                getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
            ))
        print(r.text)

    def delete(self):
        self.solr.delete(id=self._get_solr_id(), commit=True)

    def _get_isad(self, isad_id):
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
        self._index_record()
        self._store_json()
        self._remove_duplicates()

    def _index_record(self):
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

    def _get_parent_unit(self):
        if self.isad.description_level == 'SF':
            return self.isad.archival_unit.get_fonds().title_full
        if self.isad.description_level == 'S':
            return self.isad.archival_unit.get_subfonds().title_full
        return None

    def _get_date_created_display(self):
        if self.isad.year_from > 0:
            date = str(self.isad.year_from)

            if self.isad.year_to:
                if self.isad.year_from != self.isad.year_to:
                    date = date + " - " + str(self.isad.year_to)
        else:
            date = ""
        return date

    def _get_date_created_facet(self):
        date = []

        if self.isad.year_to:
            for year in range(self.isad.year_from, self.isad.year_to + 1):
                date.append(year)
        else:
            date.append(str(self.isad.year_from))

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
            sf = self.isad.archival_unit.get_subfonds()
            if sf.subfonds != 0:
                return "%s %s" % (sf.reference_code, sf.title)
            else:
                return None
        else:
            return None

    def _get_title(self, locale):
        if locale == 'en':
            return self.isad.title
        else:
            if self.isad.archival_unit.original_locale_id == locale.upper():
                return getattr(self.isad.archival_unit, "title_original")
            else:
                return None

    def _get_contents_summary_search_values(self, locale):
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
        for k, v in self.doc.items():
            if isinstance(v, list):
                self.doc[k] = list(set(v))

    def _store_json(self):
        pass
