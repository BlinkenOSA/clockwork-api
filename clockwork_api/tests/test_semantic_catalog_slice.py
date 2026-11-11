from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout

from finding_aids.management.commands.index_semantic_catalog_slice import Command, EmbeddingClient


COMMAND_MODULE = "finding_aids.management.commands.index_semantic_catalog_slice"


@override_settings(
    SEMANTIC_EMBEDDING_USERNAME="", SEMANTIC_EMBEDDING_PASSWORD="",
    SEMANTIC_SOLR_USERNAME="", SEMANTIC_SOLR_PASSWORD="",
)
class SemanticCatalogSliceTests(SimpleTestCase):
    @override_settings(REQUESTS_TIMEOUT=5, SEMANTIC_SOLR_TIMEOUT=60, SEMANTIC_SOLR_MAX_RETRIES=5)
    def test_solr_defaults_are_independent_of_global_request_timeout(self):
        options = Command().create_parser("manage.py", "index_semantic_catalog_slice").parse_args(["--all"])
        self.assertEqual(options.solr_timeout, 60)
        self.assertEqual(options.solr_max_retries, 5)

    @override_settings(SEMANTIC_SOLR_TIMEOUT=90, SEMANTIC_SOLR_MAX_RETRIES=3)
    def test_solr_settings_can_be_overridden_by_flags(self):
        parser = Command().create_parser("manage.py", "index_semantic_catalog_slice")
        defaults = parser.parse_args(["--all"])
        self.assertEqual((defaults.solr_timeout, defaults.solr_max_retries), (90, 3))
        overrides = parser.parse_args(["--all", "--solr-timeout", "120", "--solr-max-retries", "0"])
        self.assertEqual((overrides.solr_timeout, overrides.solr_max_retries), (120, 0))

    def test_invalid_solr_options_are_rejected_before_loading_records(self):
        for options, message in (
            ({"solr_timeout": 0}, "--solr-timeout must be greater than zero."),
            ({"solr_timeout": -1}, "--solr-timeout must be greater than zero."),
            ({"solr_max_retries": -1}, "--solr-max-retries must be zero or greater."),
        ):
            with self.subTest(options=options), patch.object(Command, "_get_archival_units") as load, patch(
                COMMAND_MODULE + ".requests.post"
            ) as post, self.assertRaisesMessage(CommandError, message):
                call_command("index_semantic_catalog_slice", all=True, **options)
            load.assert_not_called()
            post.assert_not_called()

    @override_settings(SEMANTIC_SOLR_TIMEOUT=60, SEMANTIC_SOLR_MAX_RETRIES=5)
    def test_transient_solr_failures_retry_the_same_document(self):
        for failure in (
            ReadTimeout("slow Solr"), ConnectTimeout("slow connection"), ConnectionError("connection reset"),
            *(Mock(status_code=status, text="temporarily unavailable") for status in (408, 429, 500, 502, 503, 504)),
        ):
            with self.subTest(failure=failure), patch(
                COMMAND_MODULE + ".requests.post", side_effect=[failure, Mock(status_code=200)],
            ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
                errors = StringIO()
                command = Command(stderr=errors)
                doc = {"id": "fa-2", "semantic_vector": [0.1, 0.2]}
                command._send_to_solr("https://solr.test/solr/catalog", doc, None, "fa-2")
                self.assertEqual(post.call_args_list, [call(
                    "https://solr.test/solr/catalog/update/json/docs/", timeout=60, json=doc, auth=None,
                )] * 2)
                sleep.assert_called_once_with(1)
                self.assertIn("document fa-2", errors.getvalue())
                self.assertIn("retry 1/5", errors.getvalue())

    def test_permanent_solr_errors_fail_immediately_with_response_details(self):
        for status in (400, 401, 403, 404, 409, 422):
            with self.subTest(status=status), patch(
                COMMAND_MODULE + ".requests.post", return_value=Mock(status_code=status, text="invalid request"),
            ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
                command = Command()
                with self.assertRaisesMessage(CommandError, "Solr document fa-2 failed with HTTP %s:\ninvalid request" % status):
                    command._send_to_solr("https://solr.test/solr/catalog", {"id": "fa-2"}, None, "fa-2")
                post.assert_called_once()
                sleep.assert_not_called()

    @override_settings(SEMANTIC_SOLR_MAX_RETRIES=7)
    def test_exhausted_timeouts_stop_with_document_id_and_capped_backoff(self):
        failure = ReadTimeout("slow Solr")
        with patch(COMMAND_MODULE + ".requests.post", side_effect=failure) as post, patch(
            COMMAND_MODULE + ".time.sleep",
        ) as sleep:
            command = Command(stderr=StringIO())
            with self.assertRaisesMessage(CommandError, "Solr document fa-2 failed after 8 attempt(s): ReadTimeout") as error:
                command._send_to_solr("https://solr.test/solr/catalog", {"id": "fa-2"}, None, "fa-2")
            self.assertIs(error.exception.__cause__, failure)
            self.assertEqual(post.call_count, 8)
            self.assertEqual(sleep.call_args_list, [call(delay) for delay in (1, 2, 4, 8, 16, 30, 30)])

    @override_settings(SEMANTIC_SOLR_MAX_RETRIES=0)
    def test_retries_can_be_disabled(self):
        with patch(COMMAND_MODULE + ".requests.post", side_effect=ReadTimeout()) as post, patch(
            COMMAND_MODULE + ".time.sleep",
        ) as sleep:
            with self.assertRaisesMessage(CommandError, "Solr document fa-2 failed after 1 attempt(s)"):
                Command()._send_to_solr("https://solr.test/solr/catalog", {"id": "fa-2"}, None, "fa-2")
            post.assert_called_once()
            sleep.assert_not_called()

    @override_settings(SEMANTIC_SOLR_MAX_RETRIES=2)
    def test_failed_commit_reports_exhaustion_without_success_message(self):
        with patch(
            COMMAND_MODULE + ".requests.post", side_effect=lambda *args, **kwargs: Mock(status_code=503, text="overloaded"),
        ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
            output = StringIO()
            command = Command(stdout=output, stderr=StringIO())
            with self.assertRaisesMessage(CommandError, "Solr commit failed after 3 attempt(s): HTTP 503:\noverloaded"):
                command._commit("https://solr.test/solr/catalog", None)
            self.assertEqual(post.call_count, 3)
            self.assertEqual(sleep.call_args_list, [call(1), call(2)])
            self.assertNotIn("Committed", output.getvalue())

    def test_command_recovers_document_and_commit_without_regenerating_embedding(self):
        record = SimpleNamespace(id=2, published=True, archival_reference_code="FA 2")
        with patch.object(Command, "_get_archival_units") as units, patch.object(
            Command, "_get_finding_aids_entities",
        ) as entities, patch.object(Command, "_build_finding_aids_semantic_text", return_value="record text"), patch(
            COMMAND_MODULE + ".FindingAidsSemanticIndexer",
        ) as indexer, patch.object(EmbeddingClient, "embed_document", return_value=[0.1]) as embed, patch(
            COMMAND_MODULE + ".requests.post",
            side_effect=[ReadTimeout(), Mock(status_code=200), ReadTimeout(), Mock(status_code=200)],
        ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
            units.return_value.iterator.return_value = iter([SimpleNamespace(level="F")])
            entities.return_value.iterator.return_value = iter([record])
            indexer.return_value.doc = {"id": "fa-2"}
            output, errors = StringIO(), StringIO()
            call_command(
                "index_semantic_catalog_slice", all=True, solr_timeout=120, solr_max_retries=2,
                stdout=output, stderr=errors,
            )
            embed.assert_called_once_with("record text")
            self.assertEqual(post.call_count, 4)
            document, retried_document, commit, retried_commit = post.call_args_list
            self.assertEqual(document, retried_document)
            self.assertEqual(commit, retried_commit)
            self.assertEqual(document.kwargs["json"], {"id": "fa-2", "semantic_vector": [0.1]})
            self.assertEqual(commit.kwargs["params"], {"commit": "true"})
            self.assertTrue(all(request.kwargs["timeout"] == 120 for request in post.call_args_list))
            self.assertEqual(sleep.call_args_list, [call(1), call(1)])
            self.assertIn("Processed 1 document(s).", output.getvalue())
            self.assertIn("Committed Solr changes.", output.getvalue())
            self.assertIn("Solr document fa-2 failed", errors.getvalue())
            self.assertIn("Solr commit failed", errors.getvalue())

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
