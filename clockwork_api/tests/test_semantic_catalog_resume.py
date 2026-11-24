from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.management.commands.index_semantic_catalog_slice import Command
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


COMMAND_MODULE = "finding_aids.management.commands.index_semantic_catalog_slice"


@override_settings(
    SEMANTIC_EMBEDDING_USERNAME="", SEMANTIC_EMBEDDING_PASSWORD="",
    SEMANTIC_SOLR_USERNAME="", SEMANTIC_SOLR_PASSWORD="",
)
class SemanticCatalogResumeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Insert out of hierarchy order; bulk insertion avoids indexing signals.
        units = []
        for fonds, subfonds, series, level in (
            (301, 0, 0, "F"), (300, 1, 10, "S"), (300, 1, 9, "S"),
            (300, 1, 2, "S"), (300, 1, 1, "S"), (300, 0, 0, "F"),
            (300, 1, 0, "SF"), (300, 2, 0, "SF"), (300, 2, 1, "S"),
            (300, 10, 1, "S"), (299, 9, 9, "S"), (300, 0, 0, "S"),
        ):
            unit = ArchivalUnit(fonds=fonds, subfonds=subfonds, series=series, level=level, title="Unit")
            unit.set_reference_code()
            units.append(unit)
        ArchivalUnit.objects.bulk_create(units)
        cls.units = {unit.reference_code: unit for unit in units}
        cls.start = cls.units["HU OSA 300-1-2"]
        Isad.objects.bulk_create([
            Isad(
                archival_unit=unit, title=unit.title, reference_code=unit.reference_code,
                description_level=unit.level, year_from=2000, published=True,
            ) for unit in units
        ])
        carrier = CarrierType.objects.create(type="Box", width=125)
        primary_type = PrimaryType.objects.create(type="Text")
        boxes = {}
        for reference_code, numbers in (
            ("HU OSA 300-1-2", (25, 10, 2, 0)),
            ("HU OSA 300-1-9", (2, 1)),
            ("HU OSA 300-1-10", (1,)),
            ("HU OSA 300-1-1", (99,)),
        ):
            for number in numbers:
                box = Container(archival_unit=cls.units[reference_code], carrier_type=carrier, container_no=number)
                boxes[reference_code, number] = box
        Container.objects.bulk_create(list(boxes.values()))
        records = []
        for title, reference_code, number, folder, sequence, template in (
            ("start 10 folder 2", "HU OSA 300-1-2", 10, 2, 1, False),
            ("start 25", "HU OSA 300-1-2", 25, 1, 0, False),
            ("start 10 item 2", "HU OSA 300-1-2", 10, 1, 2, False),
            ("start 10 item 1", "HU OSA 300-1-2", 10, 1, 1, False),
            ("start 10 item 1 tie", "HU OSA 300-1-2", 10, 1, 1, False),
            ("start 2", "HU OSA 300-1-2", 2, 1, 0, False),
            ("start 0", "HU OSA 300-1-2", 0, 1, 0, False),
            ("start no container", "HU OSA 300-1-2", None, 1, 0, False),
            ("template", "HU OSA 300-1-2", 10, 1, 0, True),
            ("later 2", "HU OSA 300-1-9", 2, 1, 0, False),
            ("later 1", "HU OSA 300-1-9", 1, 1, 0, False),
            ("later no container", "HU OSA 300-1-9", None, 1, 0, False),
            ("series 10", "HU OSA 300-1-10", 1, 1, 0, False),
            ("earlier 99", "HU OSA 300-1-1", 99, 1, 0, False),
        ):
            records.append(FindingAidsEntity(
                archival_unit=cls.units[reference_code], container=boxes.get((reference_code, number)),
                primary_type=primary_type, title=title, folder_no=folder, sequence_no=sequence,
                date_from="2000-01-01", access_rights=None, is_template=template, published=True,
            ))
        FindingAidsEntity.objects.bulk_create(records)

    def _select_units(self, *arguments):
        command = Command()
        options = vars(command.create_parser("manage.py", "index_semantic_catalog_slice").parse_args(arguments))
        command._validate_scope(options)
        return list(command._get_archival_units(options))

    def test_series_resume_uses_numeric_hierarchy_and_includes_later_fonds(self):
        selected = self._select_units("--all", "--from-series", "HU OSA 300-1-9")
        self.assertEqual([unit.reference_code for unit in selected], [
            "HU OSA 300-1-9", "HU OSA 300-1-10", "HU OSA 300-2", "HU OSA 300-2-1",
            "HU OSA 300-10-1", "HU OSA 301",
        ])

    def test_zero_series_is_included_without_reindexing_its_fonds_record(self):
        selected = self._select_units("--all", "--from-series", "HU OSA 300-0-0")
        self.assertEqual(selected[0].reference_code, "HU OSA 300-0-0")
        self.assertNotIn("HU OSA 300", [unit.reference_code for unit in selected])

    def test_from_fonds_can_include_the_starting_series(self):
        selected = self._select_units("--all", "--from-fonds", "300", "--from-series", " HU OSA 300-1-2 ")
        self.assertEqual(selected[0].pk, self.start.pk)

    def test_unknown_or_excluded_series_fails_before_any_http_requests(self):
        for reference_code, extra in (
            ("HU OSA 999-1-1", {}), ("HU OSA 300", {}), ("HU OSA 300-1-2", {"from_fonds": 301}),
        ):
            with self.subTest(reference_code=reference_code, extra=extra), patch(COMMAND_MODULE + ".requests.post") as post:
                with self.assertRaisesMessage(CommandError, "No series found in the requested scope"):
                    call_command("index_semantic_catalog_slice", all=True, from_series=reference_code, **extra)
                post.assert_not_called()

    def test_container_resume_only_limits_the_starting_series(self):
        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run), patch.object(Command, "_index_isad", return_value=1) as isad, patch.object(
                Command, "_index_finding_aids_entity", return_value=1,
            ) as finding_aid, patch.object(Command, "_commit") as commit, patch(COMMAND_MODULE + ".requests.post") as post:
                call_command(
                    "index_semantic_catalog_slice", all=True, from_series="HU OSA 300-1-2", from_container=10,
                    dry_run=dry_run, stdout=StringIO(),
                )
                self.assertEqual([request.args[0].title for request in finding_aid.call_args_list], [
                    "start 10 item 1", "start 10 item 1 tie", "start 10 item 2", "start 10 folder 2", "start 25",
                    "later no container", "later 1", "later 2", "series 10",
                ])
                self.assertEqual(isad.call_args_list[0].args[0].archival_unit_id, self.start.pk)
                self.assertEqual(commit.call_count, 0 if dry_run else 1)
                post.assert_not_called()

    def test_series_resume_without_container_reindexes_all_its_containers(self):
        with patch.object(Command, "_index_isad", return_value=1), patch.object(
            Command, "_index_finding_aids_entity", return_value=1,
        ) as finding_aid, patch.object(Command, "_commit"):
            call_command("index_semantic_catalog_slice", all=True, from_series="HU OSA 300-1-2", stdout=StringIO())
        titles = [request.args[0].title for request in finding_aid.call_args_list]
        self.assertIn("start no container", titles)
        self.assertIn("start 0", titles)
        self.assertIn("start 2", titles)
        self.assertNotIn("earlier 99", titles)
        self.assertNotIn("template", titles)

    def test_exact_series_scope_accepts_inclusive_zero_or_missing_container_numbers(self):
        for number, expected in (
            (0, ["start 0", "start 2", "start 10 item 1", "start 10 item 1 tie", "start 10 item 2", "start 10 folder 2", "start 25"]),
            (11, ["start 25"]), (26, []),
        ):
            with self.subTest(number=number), patch.object(Command, "_index_isad", return_value=1), patch.object(
                Command, "_index_finding_aids_entity", return_value=1,
            ) as finding_aid, patch.object(Command, "_commit"):
                call_command(
                    "index_semantic_catalog_slice", fonds=300, subfonds=1, series=2, from_container=number,
                    stdout=StringIO(),
                )
                self.assertEqual([request.args[0].title for request in finding_aid.call_args_list], expected)
