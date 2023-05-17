# encoding: utf-8
import json

import pysolr
from django.db.models import Sum, Count
from django.conf import settings
from hashids import Hashids
from requests.auth import HTTPBasicAuth

from container.models import Container
from controlled_list.models import Locale
from isad.models import Isad


class ISADCatalogIndexer:
    """
    Class to handle the indexing of an ISAD(G) record.
    """
    def __init__(self, isad_id):
        self.isad_id = isad_id
        self.isad = None
        self.hashids = Hashids(salt="osaarchives", min_length=8)
        self.json = {}
        self.doc = {}
        self.solr_core = getattr(settings, "SOLR_CORE_CATALOG")
        self.solr_url = "%s/%s" % (getattr(settings, "SOLR_URL"), self.solr_core)
        self.solr = pysolr.Solr(self.solr_url, always_commit=True, auth=HTTPBasicAuth(
            getattr(settings, "SOLR_USERNAME"), getattr(settings, "SOLR_PASSWORD")
        ))
        
    def get_solr_document(self):
        return self.doc

    def index(self):
        self.create_solr_document()
        try:
            self.solr.add(self.doc)
            print("Indexed ISAD(G) %s!" % self.isad.reference_code)
        except pysolr.SolrError as e:
            print('Error with ISAD(G) %s! Error: %s' % (self.isad.reference_code, e))

    def delete(self):
        self.solr.delete(id=self.get_solr_id(), commit=True)

    def create_solr_document(self):
        self._get_isad_record()
        self._make_solr_document()
        self._make_json()
        if self.isad.original_locale_id:
            self._make_json(locale_id=self.isad.original_locale_id)
        self.doc["isad_json"] = json.dumps(self.json)

    def get_solr_id(self):
        return self.hashids.encode(
            self.isad.archival_unit.fonds * 1000000 +
            self.isad.archival_unit.subfonds * 1000 +
            self.isad.archival_unit.series
        )

    def _get_isad_record(self):
        self.isad = Isad.objects.get(id=self.isad_id)

    def _make_solr_document(self):
        level = self._return_description_level(self.isad.description_level)
        self.doc['id'] = self.get_solr_id()
        self.doc['ams_id'] = self.isad.archival_unit.id
        self.doc['record_origin'] = 'Archives'
        self.doc['record_origin_facet'] = 'Archives'
        self.doc['archival_level'] = 'Archival Unit'
        self.doc['archival_level_facet'] = 'Archival Unit'

        self.doc['reference_code'] = self.isad.reference_code
        self.doc['reference_code_sort'] = self.isad.reference_code
        self.doc['archival_reference_number_search'] = self.isad.reference_code

        self.doc['title'] = self.isad.title
        self.doc['title_e'] = self.isad.title
        self.doc['title_search'] = self.isad.title
        self.doc['title_sort'] = self.isad.title

        self.doc['description_level'] = level
        self.doc['description_level_facet'] = level

        self.doc['date_created'] = self._make_date_created_display(self.isad.year_from, self.isad.year_to)
        self.doc['date_created_search'] = self._make_date_created_search(self.isad.year_from, self.isad.year_to)
        self.doc['date_created_facet'] = self._make_date_created_search(self.isad.year_from, self.isad.year_to)

        self.doc['fonds'] = int(self.isad.archival_unit.fonds)
        self.doc['fonds_sort'] = int(self.isad.archival_unit.fonds)
        self.doc['subfonds'] = int(self.isad.archival_unit.subfonds)
        self.doc['subfonds_sort'] = int(self.isad.archival_unit.subfonds)
        self.doc['series'] = int(self.isad.archival_unit.series)
        self.doc['series_sort'] = int(self.isad.archival_unit.series)

        if level == "Fonds":
            self.doc['fonds_name'] = self.isad.archival_unit.get_fonds().title_full
        elif level == "Subfonds":
            self.doc['subfonds_name'] = self.isad.archival_unit.get_subfonds().title_full

        self.doc['scope_and_content_abstract_search'] = self.isad.scope_and_content_abstract
        self.doc['scope_and_content_narrative_search'] = self.isad.scope_and_content_narrative
        self.doc['archival_history_search'] = self.isad.archival_history
        self.doc['administrative_history_search'] = self.isad.administrative_history
        self.doc["publication_note_search"] = self.isad.publication_note

        self.doc['primary_type'] = "Archival Unit"
        self.doc['primary_type_facet'] = "Archival Unit"

        self.doc['language'] = ", ".join(l.language for l in self.isad.language.all())
        self.doc['language_facet'] = list(map(lambda l: l.language, self.isad.language.all()))

        creators = list(c.creator for c in self.isad.isadcreator_set.all())
        if self.isad.isaar:
            creators.extend(list(self.isad.isaar.name))
        self.doc['creator'] = ", ".join(creators)
        self.doc['creator_facet'] = creators

        self.doc['archival_unit_theme'] = ", ".join(t.theme for t in self.isad.archival_unit.theme.all())
        self.doc['archival_unit_theme_facet'] = list(map(lambda t: t.theme, self.isad.archival_unit.theme.all()))

        if self.isad.original_locale_id:
            locale = self.isad.original_locale_id.lower()

            if self.isad.archival_unit.title_original:
                self.doc['title_search_%s' % locale] = self.isad.archival_unit.title_original
                self.doc['title_original'] = self.isad.archival_unit.title_original
                self.doc['title_original_e'] = self.isad.archival_unit.title_original

            if self.isad.scope_and_content_narrative_original:
                self.doc['scope_and_content_narrative_search_hu'] = self.isad.scope_and_content_narrative_original

            if self.isad.archival_history_original:
                self.doc['archival_history_search_%s' % locale] = self.isad.archival_history_original

            if self.isad.administrative_history_original:
                self.doc['administrative_history_search_%s' % locale] = self.isad.administrative_history_original

            if self.isad.publication_note_original:
                self.doc['publication_note_search_%s' % locale] = self.isad.publication_note_original

    def _make_json(self, locale_id='en'):
        locale = locale_id.lower()

        j = {}

        j['id'] = self.doc['id']
        j['referencde_code'] = self.isad.reference_code
        j["descriptionLevel"] = self.doc['description_level']

        j["dateFrom"] = self.isad.year_from
        j["dateTo"] = self.isad.year_to
        j["datePredominant"] = self.isad.date_predominant

        j["accruals"] = self.isad.accruals
        j["referenceCode"] = self.isad.reference_code

        j["languages"] = [l.language for l in self.isad.language.all()]

        if self.isad.access_rights:
            j["rightsAccess"] = self.isad.access_rights.statement

        if self.isad.access_rights_legacy:
            j["rightsAccess"] = self.isad.access_rights_legacy

        if self.isad.reproduction_rights:
            j["rightsReproduction"] = self.isad.reproduction_rights.statement

        if self.isad.reproduction_rights_legacy:
            j["rightsReproduction"] = self.isad.reproduction_rights_legacy

        creator = []
        for c in self.isad.isadcreator_set.all():
            creator.append(c.creator)

        if self.isad.isaar:
            creator.append(self.isad.isaar.name)
        j["creator"] = creator

        related_finding_aids = []
        for rfa in self.isad.isadrelatedfindingaids_set.all():
            related_finding_aids.append({'info': rfa.info, 'url': rfa.url})
        j["relatedUnits"] = related_finding_aids

        j["rightsReproduction"] = self.isad.reproduction_rights_legacy

        if locale == 'en':
            j["title"] = self.isad.title
            j["archivalHistory"] = self.isad.archival_history
            j["scopeAndContentNarrative"] = self.isad.scope_and_content_narrative.replace('\n', '<br />') \
                if self.isad.scope_and_content_narrative else None
            j["scopeAndContentAbstract"] = self.isad.scope_and_content_abstract.replace('\n', '<br />') \
                if self.isad.scope_and_content_abstract else None
            j["administrativeHistory"] = self.isad.administrative_history.replace('\n', '<br />') \
                if self.isad.administrative_history else None
            j["appraisal"] = self.isad.appraisal
            j["systemOfArrangement"] = self.isad.system_of_arrangement_information
            j["physicalCharacteristics"] = self.isad.physical_characteristics
            j["publicationNote"] = self.isad.publication_note
            j["note"] = self.isad.note
            j["archivistsNote"] = self.isad.archivists_note
            j["extent_estimated"] = self.isad.carrier_estimated
            j["extent"] = self._return_extent()
            j = dict((k, v) for k, v in iter(j.items()) if v)
            self.json['isad_json_eng'] = json.dumps(j)
        else:
            j["metadataLanguage"] = Locale.objects.get(pk=locale_id).locale_name
            j["metadataLanguageCode"] = locale
            j["title"] = self.isad.archival_unit.title_original
            j["archivalHistory"] = self.isad.archival_history_original
            j["scopeAndContentNarrative"] = self.isad.scope_and_content_narrative_original.replace('\n', '<br />') \
                if self.isad.scope_and_content_narrative_original else None
            j["scopeAndContentAbstract"] = self.isad.scope_and_content_abstract_original.replace('\n', '<br />') \
                if self.isad.scope_and_content_abstract_original else None
            j["administrativeHistory"] = self.isad.administrative_history_original.replace('\n', '<br />') \
                if self.isad.administrative_history_original else None
            j["appraisal"] = self.isad.appraisal_original
            j["systemOfArrangement"] = self.isad.system_of_arrangement_information_original
            j["physicalCharacteristics"] = self.isad.physical_characteristics_original
            j["publicationNote"] = self.isad.publication_note_original
            j["note"] = self.isad.note_original
            j["archivistsNote"] = self.isad.archivists_note_original
            j["extent_estimated"] = self.isad.carrier_estimated_original if locale_id == 'HU' else self.isad.carrier_estimated
            j["extent"] = self._return_extent(lang=locale_id.lower())

            if self.isad.access_rights_legacy:
                j["rightsAccess"] = self.isad.access_rights_legacy_original

            j = dict((k, v) for k, v in iter(j.items()) if v)
            self.json['isad_json_2nd'] = json.dumps(j)

    def _make_date_created_search(self, year_from, year_to):
        date = []

        if year_to:
            for year in range(year_from, year_to + 1):
                date.append(year)
        else:
            date.append(str(year_from))

        return date

    def _make_date_created_display(self, year_from, year_to):
        if year_from > 0:
            date = str(year_from)

            if year_to:
                if year_from != year_to:
                    date = date + " - " + str(year_to)
        else:
            date = ""

        return date

    def _return_description_level(self, description_level):
        levels = {
            'F': 'Fonds',
            'SF': 'Subfonds',
            'S': 'Series'
        }
        return levels[description_level]

    def _return_extent(self, lang='en'):
        extent = []
        total = 0

        archival_unit = self.isad.archival_unit

        if archival_unit.level == 'F':
            containers = Container.objects.filter(archival_unit__fonds=archival_unit.fonds)
        elif archival_unit.level == 'SF':
            containers = Container.objects.filter(archival_unit__fonds=archival_unit.fonds,
                                                  archival_unit__subfonds=archival_unit.subfonds)
        else:
            containers = Container.objects.filter(archival_unit=archival_unit)

        containers = containers.values('carrier_type__type', 'carrier_type__type_original_language')\
            .annotate(width=Sum('carrier_type__width'), number=Count('id'))

        for c in containers:
            if lang == 'hu':
                if c['carrier_type__type_original_language']:
                    extent.append(str(c['number']) + ' ' + c['carrier_type__type_original_language'] + ', ' +
                                  str(round(c['width']/1000.00, 2)) + u' folyóméter')
                else:
                    extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                                  str(round(c['width']/1000.00, 2)) + u' folyóméter')
            elif lang == 'pl':
                extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                              str(round(c['width']/1000.00, 2)) + u' metr bieżący')
            elif lang == 'it':
                extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                              str(round(c['width']/1000.00, 2)) + u' metro lineare')
            else:
                extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                              str(round(c['width']/1000.00, 2)) + ' linear meters')

        return extent
