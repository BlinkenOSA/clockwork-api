# encoding: utf-8
import json
from base64 import b64encode

import pysolr
from django.conf import settings
from hashids import Hashids

from controlled_list.models import Locale
from finding_aids.models import FindingAidsEntity
from requests.auth import HTTPBasicAuth


class FindingAidsCatalogIndexer:
    """
    Class to handle the indexing of a Finding Aids record.
    """
    def __init__(self, finding_aids_entity_id):
        self.finding_aids_id = finding_aids_entity_id
        self.finding_aids = FindingAidsEntity.objects.get(id=finding_aids_entity_id)
        self.hashids = Hashids(salt="osacontent", min_length=10)
        self.original_locale = ""
        self.json = {}
        self.doc = {}
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG", "osacatalog")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL", "http://localhost:8983/solr"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, always_commit=True, auth=HTTPBasicAuth(
            getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
        ))

    def get_solr_document(self):
        return self.doc

    def index(self):
        if self.finding_aids.confidential:
            self.create_solr_document_confidential()
        else:
            self.create_solr_document()
        try:
            self.solr.add(self.doc)
            print("Indexed FA Entity %s!" % self.finding_aids.archival_reference_code)
        except pysolr.SolrError as e:
            print('Error with FA Entity %s! Error: %s' % (self.finding_aids.archival_reference_code, e))

    def delete(self):
        self.solr.delete(id=self.get_solr_id())
        print("Deleted FA Entity %s!" % self.finding_aids.archival_reference_code)

    def create_solr_document(self):
        self._get_original_locale()
        self._make_solr_document()
        self._make_json()
        if self.original_locale != "":
            self._make_json(lang=self.original_locale)
        self.doc["item_json"] = json.dumps(self.json)
        self.doc["item_json_e"] = b64encode(json.dumps(self.json).encode("utf-8")).decode("utf-8")

    def create_solr_document_confidential(self):
        self._make_solr_confidential_document()
        self._make_confidential_json()
        self.doc["item_json"] = json.dumps(self.json)
        self.doc["item_json_e"] = b64encode(json.dumps(self.json).encode("utf-8")).decode("utf-8")

    def get_solr_id(self):
        if self.finding_aids.catalog_id:
            return self.finding_aids.catalog_id
        else:
            return self.hashids.encode(self.finding_aids.id)

    def _get_original_locale(self):
        if self.finding_aids.original_locale and \
            (self.finding_aids.contents_summary_original or
             self.finding_aids.physical_description_original or
             self.finding_aids.language_statement_original or
             self.finding_aids.note_original):
            self.original_locale = self.finding_aids.original_locale.id.lower()

    def _make_solr_document(self):
        self.doc["id"] = self.get_solr_id()
        self.doc["record_origin"] = "Archives"
        self.doc["record_origin_facet"] = "Archives"
        self.doc["call_number"] = self.finding_aids.archival_reference_code

        self.doc["archival_reference_number_search"] = [
            self.finding_aids.archival_reference_code,
            "%s:%s" % (self.finding_aids.archival_unit.reference_code, self.finding_aids.container.container_no)
        ]

        self.doc["archival_level"] = "Folder/Item"
        self.doc["archival_level_facet"] = "Folder/Item"

        self.doc["description_level"] = "Folder" if self.finding_aids.level == 'F' else 'Item'
        self.doc["description_level_facet"] = "Folder" if self.finding_aids.level == 'F' else 'Item'

        self.doc["title"] = self.finding_aids.title
        self.doc["title_e"] = self.finding_aids.title
        self.doc["title_search"] = self.finding_aids.title
        self.doc["title_sort"] = self.finding_aids.title

        self.doc["title_original_search"] = self.finding_aids.title_original if self.finding_aids.title_original else None

        self.doc["fonds_sort"] = self.finding_aids.archival_unit.fonds
        self.doc["subfonds_sort"] = self.finding_aids.archival_unit.subfonds
        self.doc["series_sort"] = self.finding_aids.archival_unit.series

        self.doc["container_type"] = self.finding_aids.container.carrier_type.type
        self.doc["container_type_esort"] = self.finding_aids.container.carrier_type.id

        self.doc["container_number"] = self.finding_aids.container.container_no
        self.doc["container_number_sort"] = self.finding_aids.container.container_no

        self.doc["folder_number"] = self.finding_aids.folder_no
        self.doc["folder_number_sort"] = self.finding_aids.folder_no

        self.doc["sequence_number"] = self.finding_aids.sequence_no
        self.doc["sequence_number_sort"] = self.finding_aids.sequence_no

        self.doc["series_id"] = self._get_series_id()
        self.doc["series_name"] = self.finding_aids.archival_unit.title_full
        self.doc["series_reference_code"] = self.finding_aids.archival_unit.reference_code.replace('HU OSA', '')

        self.doc["contents_summary_search"] = self.finding_aids.contents_summary

        self.doc["primary_type"] = self.finding_aids.primary_type.type
        self.doc["primary_type_facet"] = self.finding_aids.primary_type.type

        date_created_display = self._make_date_created_display()
        if date_created_display != "":
            self.doc["date_created"] = date_created_display

        date_created_search = self._make_date_created_search()
        if date_created_search:
            self.doc["date_created_facet"] = date_created_search
            self.doc["date_created_search"] = date_created_search

        self.doc["duration"] = self._calculate_duration(self.finding_aids.duration)

        genres = list(map(lambda g: str(g), self.finding_aids.genre.all()))
        self.doc["genre_facet"] = genres

        languages = list(
            map(lambda l: str(l.language), self.finding_aids.findingaidsentitylanguage_set.all())
        )
        self.doc["language_facet"] = languages

        # Associated entries
        associated_countries = list(
            map(lambda ac: str(ac.associated_country), self.finding_aids.findingaidsentityassociatedcountry_set.all())
        )
        self.doc["associated_country_search"] = associated_countries
        self.doc["added_geo_facet"] = associated_countries

        associated_places = list(
            map(lambda apl: str(apl.associated_place), self.finding_aids.findingaidsentityassociatedplace_set.all())
        )
        self.doc["associated_place_search"] = associated_places
        self.doc["added_geo_facet"] = associated_places

        associated_people = list(
            map(lambda ap: str(ap.associated_person), self.finding_aids.findingaidsentityassociatedperson_set.all())
        )
        self.doc["associated_person_search"] = associated_people
        self.doc["added_person_facet"] = associated_people

        associated_corporations = list(
            map(lambda ac: str(ac.associated_corporation), self.finding_aids.findingaidsentityassociatedcorporation_set.all())
        )
        self.doc["associated_corporation_search"] = associated_corporations
        self.doc["added_corporation_facet"] = associated_corporations

        # Subject entries

        if self.original_locale:
            locale = self.original_locale

            self.doc["title_original"] = self.finding_aids.title_original
            self.doc["title_search_%s" % locale] = self.finding_aids.title_original
            self.doc["contents_summary_search_%s" % locale] = self.finding_aids.contents_summary_original

        # Digital version & barcode
        if self.finding_aids.container.digital_version_exists:
            if self.finding_aids.container.barcode:
                self.doc['availability_facet'] = "Digitally Anywhere / With Registration"

                self.doc['digital_version_exists'] = True
                self.doc['digital_version_exists_facet'] = True

                self.doc['digital_version_barcode'] = self.finding_aids.container.barcode
                self.doc['digital_version_barcode_search'] = self.finding_aids.container.barcode
            else:
                if self.finding_aids.digital_version_exists:
                    self.doc['availability_facet'] = "Digitally Anywhere / With Registration"
                else:
                    self.doc['availability_facet'] = "In the Research Room"

                self.doc['digital_version_exists'] = False
                self.doc['digital_version_exists_facet'] = False
        else:
            self.doc['availability_facet'] = "In the Research Room"

    def _make_json(self, lang='en'):
        j = {}
        if lang == 'en':
            j['id'] = self.get_solr_id()
            j['legacyID'] = self.finding_aids.legacy_id
            j['title'] = self.finding_aids.title
            j['titleOriginal'] = self.finding_aids.title_original
            j['level'] = "Folder" if self.finding_aids.level == 'F' else 'Item'
            j['primaryType'] = self.finding_aids.primary_type.type
            j["containerNumber"] = self.finding_aids.container.container_no
            j["containerType"] = self.finding_aids.container.carrier_type.type

            digital_version_exists = False

            # Folder level indicator
            if self.finding_aids.digital_version_exists:
                digital_version_exists = True
                j['digital_version_container_barcode'] = "%s_%03d-%03d" % \
                     (
                         self.finding_aids.archival_unit.reference_code,
                         self.finding_aids.container.container_no,
                         self.finding_aids.folder_no
                     )

            # Container level indicator
            if self.finding_aids.container.digital_version_exists:
                digital_version_exists = True
                if self.finding_aids.container.barcode:
                    j['digital_version_container_barcode'] = self.finding_aids.container.barcode
                else:
                    if self.finding_aids.container.container_label:
                        j['digital_version_container_barcode'] = self.finding_aids.container.container_label
                    else:
                        j['digital_version_container_barcode'] = "%s_%03d" % \
                            (
                                self.finding_aids.archival_unit.reference_code,
                                self.finding_aids.container.container_no
                            )

            j['digital_version_exists'] = digital_version_exists
            j["seriesReferenceCode"] = self.finding_aids.archival_unit.reference_code.replace('HU OSA ', '')

            j["folderNumber"] = self.finding_aids.folder_no
            j["sequenceNumber"] = self.finding_aids.sequence_no

            j["formGenre"] = list(map(lambda g: str(g), self.finding_aids.genre.all()))
            j["note"] = self.finding_aids.note

            j["contentsSummary"] = self.finding_aids.contents_summary.replace('\n', '<br />') \
                if self.finding_aids.contents_summary else None

            j["language"] = list(map(lambda l: str(l.language), self.finding_aids.findingaidsentitylanguage_set.all()))
            j["languageStatement"] = self.finding_aids.language_statement

            time_start = self.finding_aids.time_start
            if time_start:
                ts_sec = time_start.total_seconds()
                ts_hours = ts_sec // 3600
                ts_minutes = (ts_sec % 3600) // 60
                ts_seconds = ts_sec % 60
                j["timeStart"] = "%02d:%02d:%02d" % (ts_hours, ts_minutes, ts_seconds)

            time_end = self.finding_aids.time_end
            if time_end:
                te_sec = time_end.total_seconds()
                te_hours = te_sec // 3600
                te_minutes = (te_sec % 3600) // 60
                te_seconds = te_sec % 60
                j["timeEnd"] = "%02d:%02d:%02d" % (te_hours, te_minutes, te_seconds)

            duration = self._calculate_duration(self.finding_aids.duration)
            j["duration"] = duration

            # Associated entries
            j["associatedPersonal"] = self._harmonize_roled_names(
                self.finding_aids.findingaidsentityassociatedperson_set, 'associated_person', 'role')

            j["associatedCorporation"] = self._harmonize_roled_names(
                self.finding_aids.findingaidsentityassociatedcorporation_set, 'associated_corporation', 'role'
            )

            j["associatedCountry"] = list(
                map(lambda ac: str(ac.associated_country), self.finding_aids.findingaidsentityassociatedcountry_set.all())
            )

            j["associatedPlace"] = list(
                map(lambda ap: str(ap.associated_place), self.finding_aids.findingaidsentityassociatedplace_set.all())
            )

            j["dateCreated"] = self._make_date_created_display()

            j["dates"] = []
            for date in self.finding_aids.findingaidsentitydate_set.all():
                j["dates"].append(
                    {"dateType": date.date_type.type, "date": self._make_date_display(date)}
                )

            # Subject entries
            j["spatialCoverageCountry"] = list(
                map(lambda c: str(c), self.finding_aids.spatial_coverage_country.all())
            )
            j["spatialCoveragePlace"] = list(
                map(lambda p: str(p), self.finding_aids.spatial_coverage_place.all())
            )
            j["subjectPeople"] = list(
                map(lambda p: str(p), self.finding_aids.subject_person.all())
            )
            j["subjectCorporation"] = list(
                map(lambda c: str(c), self.finding_aids.subject_corporation.all())
            )
            j["collectionSpecificTags"] = list(
                map(lambda k: str(k), self.finding_aids.subject_keyword.all())
            )

            # Remove empty json keys
            j = dict((k, v) for k, v in iter(j.items()) if v)

            self.json['item_json_eng'] = j
        else:
            j = {}
            j["metadataLanguage"] = Locale.objects.get(pk=lang.upper()).locale_name
            j["contentsSummary"] = self.finding_aids.contents_summary_original.replace('\n', '<br />') \
                if self.finding_aids.contents_summary_original else ""

            # Remove empty json keys
            j = dict((k, v) for k, v in iter(j.items()) if v)

            self.json['item_json_2nd'] = j

    def _make_solr_confidential_document(self):
        self.doc["id"] = self.get_solr_id(),
        self.doc["record_origin"] = "Archives",
        self.doc["record_origin_facet"] = "Archives",
        self.doc["call_number"] = self.finding_aids.archival_reference_code

        self.doc["archival_reference_number_search"] = [
            self.finding_aids.archival_reference_code,
            "%s:%s" % (self.finding_aids.archival_unit.reference_code, self.finding_aids.container.container_no)
        ]

        self.doc["archival_level"] = "Folder/Item",
        self.doc["archival_level_facet"] = "Folder/Item",

        self.doc["description_level"] = "Folder" if self.finding_aids.level == 'F' else 'Item'
        self.doc["description_level_facet"] = "Folder" if self.finding_aids.level == 'F' else 'Item'

        self.doc["fonds_sort"] = self.finding_aids.archival_unit.fonds
        self.doc["subfonds_sort"] = self.finding_aids.archival_unit.subfonds
        self.doc["series_sort"] = self.finding_aids.archival_unit.series

        self.doc["container_type"] = self.finding_aids.container.carrier_type.type
        self.doc["container_type_esort"] = self.finding_aids.container.carrier_type.id

        self.doc["container_number"] = self.finding_aids.container.container_no
        self.doc["container_number_sort"] = self.finding_aids.container.container_no

        self.doc["folder_number"] = self.finding_aids.folder_no
        self.doc["folder_number_sort"] = self.finding_aids.folder_no

        self.doc["sequence_number"] = self.finding_aids.sequence_no
        self.doc["sequence_number_sort"] = self.finding_aids.sequence_no

        self.doc["series_id"] = self._get_series_id()
        self.doc["series_name"] = self.finding_aids.archival_unit.title_full
        self.doc["series_reference_code"] = self.finding_aids.archival_unit.reference_code.replace('HU OSA', '')

        if self.finding_aids.confidential_display_text:
            self.doc["title"] = self.finding_aids.confidential_display_text
        else:
            self.doc["title"] = "The document is not published because of confidentiality reason."

    def _make_confidential_json(self):
        j = {}

        if self.finding_aids.confidential_display_text:
            j["title"] = self.finding_aids.confidential_display_text
        else:
            j["title"] = "The document is not published because of confidentiality reason."
        self.json['item_json_eng'] = j

        j['id'] = self.get_solr_id()
        j['level'] = "Folder" if self.finding_aids.level == 'F' else 'Item'
        j['primaryType'] = self.finding_aids.primary_type.type
        j["containerNumber"] = self.finding_aids.container.container_no
        j["containerType"] = self.finding_aids.container.carrier_type.type

        j["seriesReferenceCode"] = self.finding_aids.archival_unit.reference_code.replace('HU OSA ', '')

        j["folderNumber"] = self.finding_aids.folder_no
        j["sequenceNumber"] = self.finding_aids.sequence_no
        self.json['item_json_eng'] = j

    def _get_series_id(self):
        hashids = Hashids(salt="osaarchives", min_length=8)
        return hashids.encode(self.finding_aids.archival_unit.fonds * 1000000 +
                              self.finding_aids.archival_unit.subfonds * 1000 +
                              self.finding_aids.archival_unit.series)

    def _make_date_display(self, date_object):
        date_from = date_object.date_from
        date_to = date_object.date_to

        if len(date_to) > 0:
            return "%s - %s" % (date_from, date_to)
        else:
            return str(date_from)

    def _make_date_created_display(self):
        if len(self.finding_aids.date_from) == 0:
            return ""
        else:
            if len(self.finding_aids.date_from) == 4:
                year_from = self.finding_aids.date_from
            else:
                year_from = self.finding_aids.date_from.year

            if self.finding_aids.date_to:
                if len(self.finding_aids.date_to) == 4:
                    year_from = self.finding_aids.date_to
                else:
                    year_to = self.finding_aids.date_to.year
            else:
                year_to = None

            if year_from > 0:
                date = str(year_from)

                if year_to:
                    if year_from != year_to:
                        date = date + " - " + str(year_to)
            else:
                date = ""

            return date

    def _make_date_created_search(self):
        date = []
        if len(self.finding_aids.date_from) == 0:
            return None
        else:
            year_from = self.finding_aids.date_from.year
            if self.finding_aids.date_to:
                year_to = self.finding_aids.date_to.year
            else:
                year_to = None

            if year_from > 0:
                if year_to:
                    for year in range(year_from, year_to + 1):
                        date.append(year)
                else:
                    date.append(str(year_from))

            return date

    def _calculate_duration(self, duration):
        duration_string = []
        if duration:
            hours, remainder = divmod(duration.seconds, 3600)
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

    @staticmethod
    def _harmonize_roled_names(dataset, name_field, role_field):
        collection = {}
        for data in dataset.iterator():
            name = str(getattr(data, name_field))
            role = str(getattr(data, role_field))
            if name not in collection.keys():
                collection[name] = [role]
            else:
                collection[name].append(role)
        return [{"name": k, "role": ', '.join(v)} for (k, v) in collection.items()]