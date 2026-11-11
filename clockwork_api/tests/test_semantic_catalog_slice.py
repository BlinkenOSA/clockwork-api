from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings

from finding_aids.management.commands.index_semantic_catalog_slice import Command, EmbeddingClient


COMMAND_MODULE = "finding_aids.management.commands.index_semantic_catalog_slice"


@override_settings(
    SEMANTIC_EMBEDDING_USERNAME="", SEMANTIC_EMBEDDING_PASSWORD="",
    SEMANTIC_SOLR_USERNAME="", SEMANTIC_SOLR_PASSWORD="",
)
class SemanticCatalogSliceTests(SimpleTestCase):
    def test_scope_filters_include_only_supplied_hierarchy_numbers(self):
        for arguments, expected_filters in (
            (["--fonds", "300"], {"fonds": 300}),
            (["--fonds", "300", "--subfonds", "1"], {"fonds": 300, "subfonds": 1}),
            (["--fonds", "300", "--subfonds", "0"], {"fonds": 300, "subfonds": 0}),
            (["--fonds", "300", "--subfonds", "0", "--series", "1"],
             {"fonds": 300, "subfonds": 0, "series": 1}),
            (["--all"], {}),
        ):
            with self.subTest(arguments=arguments), patch(COMMAND_MODULE + ".ArchivalUnit.objects.filter") as filter_units:
                command = Command()
                options = vars(command.create_parser("manage.py", "index_semantic_catalog_slice").parse_args(arguments))
                command._validate_scope(options)
                selected = command._get_archival_units(options)
                filter_units.assert_called_once_with(**expected_filters)
                self.assertIs(selected, filter_units.return_value.select_related.return_value)

    def test_invalid_scopes_are_rejected_before_loading_or_sending_records(self):
        for options, message in (
            ({}, "Specify --fonds or --all."),
            ({"subfonds": 1}, "Specify --fonds or --all."),
            ({"series": 1}, "Specify --fonds or --all."),
            ({"fonds": 300, "series": 1}, "--series requires --subfonds."),
            ({"all": True, "fonds": 300}, "--all cannot be combined"),
            ({"all": True, "subfonds": 0}, "--all cannot be combined"),
            ({"all": True, "series": 1}, "--all cannot be combined"),
        ):
            with self.subTest(options=options), patch.object(Command, "_get_archival_units") as load, patch(
                COMMAND_MODULE + ".requests.post"
            ) as post, self.assertRaisesMessage(CommandError, message):
                call_command("index_semantic_catalog_slice", **options)
            load.assert_not_called()
            post.assert_not_called()

    def test_missing_hierarchy_is_rejected(self):
        with patch(COMMAND_MODULE + ".ArchivalUnit.objects.filter") as filter_units, patch(
            COMMAND_MODULE + ".requests.post"
        ) as post:
            filter_units.return_value.select_related.return_value.exists.return_value = False
            with self.assertRaisesMessage(CommandError, "No archival unit found for the requested hierarchy."):
                call_command("index_semantic_catalog_slice", fonds=300, stdout=StringIO())
            post.assert_not_called()

    def test_empty_catalog_with_all_processes_zero_documents(self):
        with patch(COMMAND_MODULE + ".ArchivalUnit.objects.filter") as filter_units, patch.object(Command, "_commit"):
            selected = filter_units.return_value.select_related.return_value
            selected.iterator.return_value = iter([])
            output = StringIO()
            call_command("index_semantic_catalog_slice", all=True, stdout=output)
            self.assertIn("Processed 0 document(s).", output.getvalue())

    def test_multiple_units_use_their_own_series_context_and_commit_once(self):
        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run):
                units = []
                for number, level in enumerate(("F", "SF", "S", "S")):
                    unit = SimpleNamespace(level=level, title="Unit %s" % number)
                    if level != "SF":
                        unit.isad = SimpleNamespace(
                            id=number, published=True, reference_code=unit.title,
                            scope_and_content_abstract="Description %s." % number,
                            scope_and_content_narrative="",
                        )
                    units.append(unit)
                finding_aids = [
                    SimpleNamespace(id=number, published=True, archival_reference_code="FA %s" % number)
                    for number in (2, 3)
                ]
                with patch.object(Command, "_get_archival_units") as load, patch.object(
                    Command, "_get_finding_aids_entities"
                ) as entities, patch.object(Command, "_build_isad_semantic_text", return_value="isad text") as isad_text, patch.object(
                    Command, "_build_finding_aids_semantic_text", return_value="fa text"
                ) as fa_text, patch(COMMAND_MODULE + ".ISADSemanticIndexer") as isad_indexer, patch(
                    COMMAND_MODULE + ".FindingAidsSemanticIndexer"
                ) as fa_indexer, patch.object(EmbeddingClient, "embed_document", return_value=[0.1]) as embed, patch(
                    COMMAND_MODULE + ".requests.post", return_value=Mock(status_code=200)
                ) as post:
                    load.return_value.iterator.return_value = iter(units)
                    entities.side_effect = [Mock(iterator=Mock(return_value=iter(records))) for records in (
                        [], [], [finding_aids[0]], [finding_aids[1]],
                    )]
                    isad_indexer.return_value.doc = {"id": "isad"}
                    fa_indexer.return_value.doc = {"id": "fa"}
                    output = StringIO()
                    call_command("index_semantic_catalog_slice", fonds=300, dry_run=dry_run, stdout=output)

                    self.assertEqual(entities.call_args_list, [call(unit) for unit in units])
                    self.assertEqual(isad_text.call_args_list, [
                        call(units[0].isad, ""),
                        call(units[2].isad, "Unit 2\nDescription 2."),
                        call(units[3].isad, "Unit 3\nDescription 3."),
                    ])
                    self.assertEqual(fa_text.call_args_list, [
                        call(finding_aids[0], "Unit 2\nDescription 2."),
                        call(finding_aids[1], "Unit 3\nDescription 3."),
                    ])
                    self.assertIn("Processed 5 document(s).", output.getvalue())
                    self.assertEqual(embed.call_count, 0 if dry_run else 5)
                    self.assertEqual(post.call_count, 0 if dry_run else 6)
                    if not dry_run:
                        self.assertEqual(post.call_args.kwargs["params"], {"commit": "true"})
