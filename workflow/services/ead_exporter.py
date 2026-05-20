from datetime import datetime
import re
from typing import Iterable, Optional
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
from zoneinfo import ZoneInfo

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class EADExporter:
    NS = "urn:isbn:1-931666-22-9"

    def __init__(self):
        register_namespace("", self.NS)

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

        root = Element(self._tag("ead"))
        self._build_header(root, file_name, container, requested_entity, fonds, series)
        archdesc = SubElement(root, self._tag("archdesc"), level="fonds")
        self._append_isad_did(archdesc, fonds)
        self._append_isad_sections(archdesc, getattr(fonds, "isad", None))

        dsc = SubElement(archdesc, self._tag("dsc"))
        parent = dsc

        if subfonds is not None and subfonds.id != fonds.id:
            parent = self._build_isad_component(parent, subfonds, "subfonds")

        series_component = self._build_isad_component(parent, series, "series")

        if container is not None:
            container_component = SubElement(
                series_component,
                self._tag("c"),
                level="otherlevel",
                otherlevel="container",
                id=self._component_id(container.archival_unit.reference_code, f"container-{container.container_no}"),
            )
            self._append_container_did(container_component, container)
            self._append_container_sections(container_component, container)

            for entity in finding_aids_entities:
                self._append_finding_aids_component(container_component, entity)

        self._indent(root)
        return tostring(root, encoding="unicode", xml_declaration=True)

    def _build_header(self, root, file_name, container, requested_entity, fonds, series):
        eadheader = SubElement(root, self._tag("eadheader"))
        eadid = SubElement(eadheader, self._tag("eadid"))
        eadid.text = file_name

        filedesc = SubElement(eadheader, self._tag("filedesc"))
        titlestmt = SubElement(filedesc, self._tag("titlestmt"))
        titleproper = SubElement(titlestmt, self._tag("titleproper"))

        if requested_entity is not None:
            titleproper.text = f"EAD export for {requested_entity.archival_reference_code}"
        elif container is not None:
            titleproper.text = f"EAD export for {container.archival_unit.reference_code}:{container.container_no}"
        else:
            titleproper.text = f"EAD export for {series.reference_code}"

        publicationstmt = SubElement(filedesc, self._tag("publicationstmt"))
        publisher = SubElement(publicationstmt, self._tag("publisher"))
        publisher.text = "Blinken OSA Archivum - archivum.org"

        profiledesc = SubElement(eadheader, self._tag("profiledesc"))
        creation = SubElement(profiledesc, self._tag("creation"))

        now = datetime.now(ZoneInfo("Europe/Budapest")).replace(microsecond=0).isoformat()
        creation.text = f"Generated from Blinken OSAs Archival Management System on {now}"

    def _build_isad_component(self, parent, archival_unit: ArchivalUnit, level: str):
        component = SubElement(
            parent,
            self._tag("c"),
            level=level,
            id=self._component_id(archival_unit.reference_code),
        )
        self._append_isad_did(component, archival_unit)
        self._append_isad_sections(component, getattr(archival_unit, "isad", None))
        return component

    def _append_isad_did(self, parent, archival_unit: ArchivalUnit):
        did = SubElement(parent, self._tag("did"))
        self._text_element(did, "unitid", archival_unit.reference_code)
        self._text_element(did, "unittitle", archival_unit.title)
        self._text_element(did, "origination", self._join_texts(self._isad_creators(getattr(archival_unit, "isad", None))))

        isad = getattr(archival_unit, "isad", None)
        if isad is not None:
            date_text = self._format_years(isad.year_from, isad.year_to)
            self._text_element(did, "unitdate", date_text)
            for extent in isad.isadextent_set.all():
                physdesc = SubElement(did, self._tag("physdesc"))
                label = f"{'approximately ' if extent.approx else ''}{extent.extent_number} {extent.extent_unit.unit}"
                self._text_element(physdesc, "extent", label)
            for carrier in isad.isadcarrier_set.all():
                physdesc = SubElement(did, self._tag("physdesc"))
                self._text_element(physdesc, "physfacet", f"{carrier.carrier_number} {carrier.carrier_type.type}")

    def _append_isad_sections(self, parent, isad: Optional[Isad]):
        if isad is None:
            return

        self._text_block(
            parent,
            "bioghist",
            isad.administrative_history,
            isad.archival_history,
        )
        self._text_block(
            parent,
            "scopecontent",
            isad.scope_and_content_abstract,
            isad.scope_and_content_narrative,
            isad.appraisal,
        )
        self._text_block(
            parent,
            "arrangement",
            isad.system_of_arrangement_information,
            self._join_texts(
                [
                    "Accruals expected" if isad.accruals else None,
                    f"Predominant dates: {isad.date_predominant}" if isad.date_predominant else None,
                ]
            ),
        )
        self._text_block(
            parent,
            "phystech",
            isad.physical_characteristics,
            isad.carrier_estimated,
        )
        self._text_block(parent, "accessrestrict", self._join_texts([
            self._value(isad.access_rights, "statement"),
            isad.access_rights_legacy,
            self._value(isad.rights_restriction_reason, "reason"),
            f"Embargo until: {isad.embargo}" if isad.embargo else None,
        ]))
        self._text_block(parent, "userestrict", self._join_texts([
            self._value(isad.reproduction_rights, "statement"),
            isad.reproduction_rights_legacy,
        ]))
        self._text_block(parent, "otherfindaid", self._join_texts(
            [self._join_texts([item.info, item.url], separator=" - ") for item in isad.isadrelatedfindingaids_set.all()]
        ))
        self._text_block(parent, "originalsloc", self._join_texts(
            [self._join_texts([item.info, item.url], separator=" - ") for item in isad.isadlocationoforiginals_set.all()]
        ))
        self._text_block(parent, "altformavail", self._join_texts(
            [self._join_texts([item.info, item.url], separator=" - ") for item in isad.isadlocationofcopies_set.all()]
        ))
        self._text_block(parent, "bibliography", isad.publication_note)
        self._text_block(
            parent,
            "note",
            isad.note,
            isad.internal_note,
            isad.archivists_note,
            isad.rules_conventions,
        )
        self._append_controlaccess(
            parent,
            languages=[language.language for language in isad.language.all()],
        )

    def _append_container_did(self, parent, container: Container):
        did = SubElement(parent, self._tag("did"))
        self._text_element(did, "unitid", f"{container.archival_unit.reference_code}:{container.container_no}")
        label = container.container_label or f"{container.carrier_type.type} #{container.container_no}"
        self._text_element(did, "unittitle", label)
        self._text_element(did, "physloc", container.barcode)
        physdesc = SubElement(did, self._tag("physdesc"))
        self._text_element(physdesc, "extent", f"1 {container.carrier_type.type}")

    def _append_container_sections(self, parent, container: Container):
        notes = self._join_texts(
            [
                f"Barcode: {container.barcode}" if container.barcode else None,
                f"Permanent ID: {container.permanent_id}" if container.permanent_id else None,
                f"Legacy ID: {container.legacy_id}" if container.legacy_id else None,
                container.internal_note,
            ]
        )
        self._text_block(parent, "odd", notes)

    def _append_finding_aids_component(self, parent, entity: FindingAidsEntity):
        level = "file" if entity.level == "F" else "item"
        component = SubElement(
            parent,
            self._tag("c"),
            level=level,
            id=self._component_id(entity.archival_reference_code),
        )
        did = SubElement(component, self._tag("did"))
        self._text_element(did, "unitid", entity.archival_reference_code)
        self._text_element(did, "unittitle", entity.title)
        self._text_element(did, "origination", self._join_texts(
            [self._join_texts([creator.creator, self._creator_role_label(creator.role)], separator=" - ")
             for creator in entity.findingaidsentitycreator_set.all()]
        ))
        self._text_element(did, "unitdate", self._format_date_range(entity.date_from, entity.date_to))

        for alt_title in entity.findingaidsentityalternativetitle_set.all():
            self._text_element(did, "unittitle", alt_title.alternative_title, {"type": "alternative"})

        for identifier in entity.findingaidsentityidentifier_set.all():
            self._text_element(
                did,
                "unitid",
                identifier.identifier,
                {"type": self._value(identifier.identifier_type, "type") or "identifier"},
            )

        for extent in entity.findingaidsentityextent_set.all():
            physdesc = SubElement(did, self._tag("physdesc"))
            self._text_element(physdesc, "extent", self._join_texts([extent.extent_number, self._value(extent.extent_unit, "unit")]))

        self._text_element(did, "materialspec", self._value(entity.primary_type, "type"))
        self._text_element(did, "langmaterial", entity.language_statement)
        self._text_element(did, "physfacet", entity.physical_condition)
        self._text_element(did, "dimensions", entity.dimensions)

        self._text_block(component, "scopecontent", entity.contents_summary)
        self._text_block(component, "bioghist", entity.administrative_history)
        self._text_block(component, "phystech", self._join_texts([entity.physical_description, self._duration_summary(entity)]))
        self._text_block(component, "accessrestrict", self._join_texts([
            self._value(entity.access_rights, "statement"),
            entity.access_rights_restriction_explanation,
            f"Restriction date: {entity.access_rights_restriction_date}" if entity.access_rights_restriction_date else None,
            entity.confidential_display_text,
        ]))
        self._text_block(component, "note", self._join_texts([entity.note, entity.internal_note]))
        self._text_block(component, "relatedmaterial", self._join_texts([
            self._join_texts(
                [
                    material.destination.archival_reference_code if material.destination_id else None,
                    material.relationship_source,
                    material.relationship_destination,
                ],
                separator=" - ",
            )
            for material in entity.relationship_sources.select_related("destination").all()
        ]))
        self._text_block(component, "dao", self._join_texts([
            "Digital version exists" if entity.digital_version_exists else None,
            "Available online" if entity.digital_version_online else None,
            "Available in Research Cloud" if entity.digital_version_research_cloud else None,
            entity.digital_version_research_cloud_path,
        ]))

        self._append_controlaccess(
            component,
            genres=[genre.genre for genre in entity.genre.all()],
            languages=[
                self._join_texts([lang.language.language, self._value(lang.language_usage, "usage")], separator=" - ")
                for lang in entity.findingaidsentitylanguage_set.select_related("language", "language_usage").all()
            ],
            subject_headings=[subject.subject for subject in entity.subject_heading.all()],
            keywords=[keyword.keyword for keyword in entity.subject_keyword.all()],
            subjects=[subject.subject for subject in entity.findingaidsentitysubject_set.all()],
            subject_people=[str(person) for person in entity.subject_person.all()],
            subject_corporations=[corp.name for corp in entity.subject_corporation.all()],
            spatial_countries=[country.country for country in entity.spatial_coverage_country.all()],
            spatial_places=[place.place for place in entity.spatial_coverage_place.all()],
            associated_people=[
                self._join_texts(
                    [str(rel.associated_person), self._value(rel.role, "role")],
                    separator=" - ",
                )
                for rel in entity.findingaidsentityassociatedperson_set.select_related("associated_person", "role").all()
            ],
            associated_corporations=[
                self._join_texts(
                    [rel.associated_corporation.name, self._value(rel.role, "role")],
                    separator=" - ",
                )
                for rel in entity.findingaidsentityassociatedcorporation_set.select_related("associated_corporation", "role").all()
            ],
            associated_countries=[
                self._join_texts(
                    [rel.associated_country.country, self._value(rel.role, "role")],
                    separator=" - ",
                )
                for rel in entity.findingaidsentityassociatedcountry_set.select_related("associated_country", "role").all()
            ],
            associated_places=[
                self._join_texts(
                    [rel.associated_place.place, self._value(rel.role, "role")],
                    separator=" - ",
                )
                for rel in entity.findingaidsentityassociatedplace_set.select_related("associated_place", "role").all()
            ],
            places_of_creation=[place.place for place in entity.findingaidsentityplaceofcreation_set.all()],
        )

    def _append_controlaccess(self, parent, **groups):
        controlaccess = None
        tag_map = {
            "genres": "genreform",
            "languages": "language",
            "subject_headings": "subject",
            "keywords": "subject",
            "subjects": "subject",
            "subject_people": "persname",
            "subject_corporations": "corpname",
            "spatial_countries": "geogname",
            "spatial_places": "geogname",
            "associated_people": "persname",
            "associated_corporations": "corpname",
            "associated_countries": "geogname",
            "associated_places": "geogname",
            "places_of_creation": "geogname",
        }

        for key, values in groups.items():
            cleaned = [value for value in values if value]
            if not cleaned:
                continue
            if controlaccess is None:
                controlaccess = SubElement(parent, self._tag("controlaccess"))
            for value in cleaned:
                self._text_element(controlaccess, tag_map[key], value)

    def _text_block(self, parent, tag, *parts):
        text = self._join_texts(parts)
        if not text:
            return
        node = SubElement(parent, self._tag(tag))
        self._text_element(node, "p", text)

    def _text_element(self, parent, tag, text, attrs=None):
        if text in (None, ""):
            return None
        node = SubElement(parent, self._tag(tag), attrs or {})
        node.text = str(text)
        return node

    def _component_id(self, reference_code: str, suffix: Optional[str] = None) -> str:
        value = reference_code if suffix is None else f"{reference_code}-{suffix}"
        return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()

    def _format_years(self, year_from, year_to):
        if year_from and year_to:
            return f"{year_from}-{year_to}"
        return year_from

    def _format_date_range(self, date_from, date_to):
        if date_from and date_to:
            return f"{date_from} - {date_to}"
        return date_from or date_to

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

    def _isad_creators(self, isad: Optional[Isad]):
        if isad is None:
            return []
        creators = list(isad.isadcreator_set.values_list("creator", flat=True))
        if isad.isaar_id:
            creators.append(isad.isaar.name)
        return creators

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

    def _tag(self, name: str) -> str:
        return f"{{{self.NS}}}{name}"

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
