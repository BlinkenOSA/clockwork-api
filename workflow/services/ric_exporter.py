import re
from typing import Iterable, Optional
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity


class RICExporter:
    RICO_NS = "https://www.ica.org/standards/RiC/ontology#"
    RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

    def __init__(self):
        register_namespace("rico", self.RICO_NS)
        register_namespace("rdf", self.RDF_NS)

    def render_for_container(self, container: Container, file_name: str) -> str:
        return self._render(
            file_name=file_name,
            archival_unit=container.archival_unit,
            container=container,
            finding_aids_entities=container.findingaidsentity_set.filter(is_template=False).order_by(
                "folder_no", "sequence_no", "id"
            ),
            requested_entity=None,
        )

    def render_for_finding_aids_entity(self, entity: FindingAidsEntity, file_name: str) -> str:
        return self._render(
            file_name=file_name,
            archival_unit=entity.archival_unit,
            container=entity.container,
            finding_aids_entities=[entity],
            requested_entity=entity,
        )

    def _render(
        self,
        *,
        file_name: str,
        archival_unit: ArchivalUnit,
        container: Optional[Container],
        finding_aids_entities: Iterable[FindingAidsEntity],
        requested_entity: Optional[FindingAidsEntity],
    ) -> str:
        fonds = archival_unit.get_fonds()
        subfonds = archival_unit.get_subfonds()
        series = archival_unit

        root = Element(self._rdf_tag("RDF"))
        self._append_export_metadata(root, file_name, requested_entity, container)

        self._append_archival_unit_record(root, fonds, "Fonds")
        current_parent_uri = self._uri(fonds)

        if subfonds is not None and subfonds.id != fonds.id:
            self._append_archival_unit_record(root, subfonds, "Subfonds", parent_uri=self._uri(fonds))
            current_parent_uri = self._uri(subfonds)

        self._append_archival_unit_record(root, series, "Series", parent_uri=current_parent_uri)

        if container is not None:
            container_uri = self._uri(container)
            self._append_container_record(root, container, parent_uri=self._uri(series))
            for entity in finding_aids_entities:
                self._append_finding_aids_record(root, entity, parent_uri=container_uri)

        self._indent(root)
        return tostring(root, encoding="unicode", xml_declaration=True)

    def _append_export_metadata(self, root, file_name, requested_entity, container):
        metadata = SubElement(root, self._rico_tag("Instantiation"))
        metadata.set(self._rdf_tag("about"), f"#export-{self._slug(file_name)}")
        self._text_element(metadata, "name", f"RiC export for {file_name}")
        self._text_element(metadata, "identifier", file_name)
        if requested_entity is not None:
            self._text_element(metadata, "generalDescription", requested_entity.archival_reference_code)
        elif container is not None:
            self._text_element(metadata, "generalDescription", f"{container.archival_unit.reference_code}:{container.container_no}")

    def _append_archival_unit_record(self, root, archival_unit: ArchivalUnit, level_label: str, parent_uri: Optional[str] = None):
        node = SubElement(root, self._rico_tag("RecordSet"))
        node.set(self._rdf_tag("about"), self._uri(archival_unit))

        isad = getattr(archival_unit, "isad", None)
        self._text_element(node, "name", archival_unit.title)
        self._text_element(node, "identifier", archival_unit.reference_code)
        self._text_element(node, "hasRecordSetType", level_label)
        self._text_element(node, "date", self._format_years(isad.year_from, isad.year_to) if isad else None)
        self._text_element(node, "history", self._join_texts([
            getattr(isad, "administrative_history", None),
            getattr(isad, "archival_history", None),
        ]))
        self._text_element(node, "scopeAndContent", self._join_texts([
            getattr(isad, "scope_and_content_abstract", None),
            getattr(isad, "scope_and_content_narrative", None),
            getattr(isad, "appraisal", None),
        ]))
        self._text_element(node, "conditionsOfAccess", self._join_texts([
            self._value(getattr(isad, "access_rights", None), "statement"),
            getattr(isad, "access_rights_legacy", None),
            self._value(getattr(isad, "rights_restriction_reason", None), "reason"),
            f"Embargo until: {getattr(isad, 'embargo', None)}" if getattr(isad, "embargo", None) else None,
        ]))
        self._text_element(node, "conditionsOfUse", self._join_texts([
            self._value(getattr(isad, "reproduction_rights", None), "statement"),
            getattr(isad, "reproduction_rights_legacy", None),
        ]))
        self._text_element(node, "physicalCharacteristics", self._join_texts([
            getattr(isad, "physical_characteristics", None),
            getattr(isad, "carrier_estimated", None),
            getattr(isad, "carrier_estimated_original", None),
        ]))
        self._text_element(node, "generalDescription", self._join_texts([
            getattr(isad, "system_of_arrangement_information", None),
            getattr(isad, "system_of_arrangement_information_original", None),
            f"Predominant dates: {getattr(isad, 'date_predominant', None)}" if getattr(isad, "date_predominant", None) else None,
            "Accruals expected" if getattr(isad, "accruals", False) else None,
            getattr(isad, "note", None),
            getattr(isad, "note_original", None),
            getattr(isad, "internal_note", None),
            getattr(isad, "internal_note_original", None),
            getattr(isad, "archivists_note", None),
            getattr(isad, "archivists_note_original", None),
            getattr(isad, "rules_conventions", None),
            getattr(isad, "publication_note", None),
            getattr(isad, "publication_note_original", None),
        ]))
        self._append_relation(node, "isOrWasIncludedIn", parent_uri)

        if isad is not None:
            for creator in isad.isadcreator_set.all():
                self._text_element(node, "hasCreator", creator.creator)
            if isad.isaar_id:
                self._text_element(node, "hasCreator", isad.isaar.name)
            for language in isad.language.all():
                self._text_element(node, "language", language.language)
            for extent in isad.isadextent_set.all():
                self._text_element(node, "extent", self._join_texts([extent.extent_number, extent.extent_unit.unit], separator=" "))
            for carrier in isad.isadcarrier_set.all():
                self._text_element(node, "carrierType", carrier.carrier_type.type)
            for related in isad.isadrelatedfindingaids_set.all():
                self._text_element(node, "findingAid", self._join_texts([related.info, related.url], separator=" - "))
            for location in isad.isadlocationoforiginals_set.all():
                self._text_element(node, "hasOrHadLocation", self._join_texts([location.info, location.url], separator=" - "))
            for location in isad.isadlocationofcopies_set.all():
                self._text_element(node, "hasOrHadLocation", self._join_texts([location.info, location.url], separator=" - "))

        return archival_unit

    def _append_container_record(self, root, container: Container, parent_uri: str):
        node = SubElement(root, self._rico_tag("Record"))
        node.set(self._rdf_tag("about"), self._uri(container))
        self._text_element(node, "name", container.container_label or f"{container.carrier_type.type} #{container.container_no}")
        self._text_element(node, "identifier", f"{container.archival_unit.reference_code}:{container.container_no}")
        self._text_element(node, "identifier", container.barcode)
        self._text_element(node, "carrierType", container.carrier_type.type)
        self._text_element(node, "physicalLocation", container.barcode)
        self._text_element(node, "generalDescription", self._join_texts([
            f"Permanent ID: {container.permanent_id}" if container.permanent_id else None,
            f"Legacy ID: {container.legacy_id}" if container.legacy_id else None,
            container.internal_note,
        ]))
        self._append_relation(node, "isOrWasIncludedIn", parent_uri)

    def _append_finding_aids_record(self, root, entity: FindingAidsEntity, parent_uri: str):
        node = SubElement(root, self._rico_tag("Record"))
        node.set(self._rdf_tag("about"), self._uri(entity))
        self._text_element(node, "name", entity.title)
        self._text_element(node, "identifier", entity.archival_reference_code)
        self._text_element(node, "hasRecordType", "Folder" if entity.level == "F" else "Item")
        self._text_element(node, "date", self._format_date_range(entity.date_from, entity.date_to))
        self._text_element(node, "scopeAndContent", entity.contents_summary)
        self._text_element(node, "history", entity.administrative_history)
        self._text_element(node, "physicalCharacteristics", self._join_texts([
            entity.physical_description,
            entity.physical_condition,
            self._duration_summary(entity),
            entity.dimensions,
        ]))
        self._text_element(node, "conditionsOfAccess", self._join_texts([
            self._value(entity.access_rights, "statement"),
            entity.access_rights_restriction_explanation,
            f"Restriction date: {entity.access_rights_restriction_date}" if entity.access_rights_restriction_date else None,
            entity.confidential_display_text,
        ]))
        self._text_element(node, "language", entity.language_statement)
        self._text_element(node, "documentaryFormType", self._value(entity.primary_type, "type"))
        self._text_element(node, "generalDescription", self._join_texts([entity.note, entity.internal_note]))
        self._append_relation(node, "isOrWasIncludedIn", parent_uri)

        for creator in entity.findingaidsentitycreator_set.all():
            self._text_element(
                node,
                "hasCreator",
                self._join_texts([creator.creator, self._creator_role_label(creator.role)], separator=" - "),
            )
        for alt_title in entity.findingaidsentityalternativetitle_set.all():
            self._text_element(node, "name", alt_title.alternative_title)
        for identifier in entity.findingaidsentityidentifier_set.select_related("identifier_type").all():
            self._text_element(
                node,
                "identifier",
                self._join_texts([self._value(identifier.identifier_type, "type"), identifier.identifier], separator=": "),
            )
        for date in entity.findingaidsentitydate_set.select_related("date_type").all():
            self._text_element(
                node,
                "date",
                self._join_texts([
                    self._value(date.date_type, "type"),
                    self._format_date_range(date.date_from, date.date_to),
                ], separator=": "),
            )
        for extent in entity.findingaidsentityextent_set.select_related("extent_unit").all():
            self._text_element(node, "extent", self._join_texts([extent.extent_number, extent.extent_unit.unit], separator=" "))
        for genre in entity.genre.all():
            self._text_element(node, "documentaryFormType", genre.genre)
        for subject in entity.subject_heading.all():
            self._text_element(node, "subject", subject.subject)
        for subject in entity.findingaidsentitysubject_set.all():
            self._text_element(node, "subject", subject.subject)
        for keyword in entity.subject_keyword.all():
            self._text_element(node, "subject", keyword.keyword)
        for person in entity.subject_person.all():
            self._text_element(node, "subject", str(person))
        for corp in entity.subject_corporation.all():
            self._text_element(node, "subject", corp.name)
        for country in entity.spatial_coverage_country.all():
            self._text_element(node, "place", country.country)
        for place in entity.spatial_coverage_place.all():
            self._text_element(node, "place", place.place)
        for place in entity.findingaidsentityplaceofcreation_set.all():
            self._text_element(node, "place", place.place)
        for language in entity.findingaidsentitylanguage_set.select_related("language", "language_usage").all():
            self._text_element(
                node,
                "language",
                self._join_texts([language.language.language, self._value(language.language_usage, "usage")], separator=" - "),
            )
        for rel in entity.findingaidsentityassociatedperson_set.select_related("associated_person", "role").all():
            self._text_element(node, "hasCreator", self._join_texts([str(rel.associated_person), self._value(rel.role, "role")], separator=" - "))
        for rel in entity.findingaidsentityassociatedcorporation_set.select_related("associated_corporation", "role").all():
            self._text_element(node, "hasCreator", self._join_texts([rel.associated_corporation.name, self._value(rel.role, "role")], separator=" - "))
        for rel in entity.findingaidsentityassociatedcountry_set.select_related("associated_country", "role").all():
            self._text_element(node, "place", self._join_texts([rel.associated_country.country, self._value(rel.role, "role")], separator=" - "))
        for rel in entity.findingaidsentityassociatedplace_set.select_related("associated_place", "role").all():
            self._text_element(node, "place", self._join_texts([rel.associated_place.place, self._value(rel.role, "role")], separator=" - "))
        for material in entity.relationship_sources.select_related("destination").all():
            self._text_element(
                node,
                "isAssociatedWith",
                self._join_texts([
                    material.destination.archival_reference_code if material.destination_id else None,
                    material.relationship_source,
                    material.relationship_destination,
                ], separator=" - "),
            )

    def _append_relation(self, node, tag_name: str, resource_uri: Optional[str]):
        if not resource_uri:
            return
        relation = SubElement(node, self._rico_tag(tag_name))
        relation.set(self._rdf_tag("resource"), resource_uri)

    def _uri(self, obj=None):
        if isinstance(obj, ArchivalUnit):
            return f"#archival-unit-{self._slug(obj.reference_code)}"
        if isinstance(obj, Container):
            return f"#container-{self._slug(obj.archival_unit.reference_code)}-{obj.container_no}"
        if isinstance(obj, FindingAidsEntity):
            return f"#finding-aids-{self._slug(obj.archival_reference_code)}"
        return None

    def _duration_summary(self, entity: FindingAidsEntity):
        parts = []
        if entity.time_start:
            parts.append(f"Start: {entity.time_start}")
        if entity.time_end:
            parts.append(f"End: {entity.time_end}")
        if entity.duration:
            parts.append(f"Duration: {entity.duration}")
        return self._join_texts(parts)

    def _creator_role_label(self, role_code: Optional[str]) -> Optional[str]:
        if role_code == "COL":
            return "Collector"
        if role_code == "CRE":
            return "Creator"
        return role_code

    def _format_years(self, year_from, year_to):
        if year_from and year_to:
            return f"{year_from}-{year_to}"
        return year_from

    def _format_date_range(self, date_from, date_to):
        if date_from and date_to:
            return f"{date_from} - {date_to}"
        return date_from or date_to

    def _value(self, obj, attr):
        return getattr(obj, attr, None) if obj is not None else None

    def _join_texts(self, parts, separator="; "):
        values = []
        for part in parts:
            if part is None:
                continue
            value = str(part).strip()
            if value:
                values.append(value)
        return separator.join(values)

    def _text_element(self, parent, tag_name, text):
        if text in (None, ""):
            return None
        node = SubElement(parent, self._rico_tag(tag_name))
        node.text = str(text)
        return node

    def _rico_tag(self, name: str) -> str:
        return f"{{{self.RICO_NS}}}{name}"

    def _rdf_tag(self, name: str) -> str:
        return f"{{{self.RDF_NS}}}{name}"

    def _slug(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()

    def _indent(self, element, level=0):
        indent = "\n" + level * "  "
        if len(element):
            if not element.text or not element.text.strip():
                element.text = indent + "  "
            for child in element:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        elif level and (not element.tail or not element.tail.strip()):
            element.tail = indent
