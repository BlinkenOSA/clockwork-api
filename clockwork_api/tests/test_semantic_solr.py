from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings
from requests.auth import HTTPBasicAuth

from clockwork_api.semantic_solr import get_semantic_solr_auth, get_semantic_solr_url
from finding_aids.indexers.finding_aids_semantic_indexer import FindingAidsSemanticIndexer
from finding_aids.management.commands.index_semantic_catalog_slice import Command, EmbeddingClient
from isad.indexers.isad_semantic_indexer import ISADSemanticIndexer


@override_settings(
    SEMANTIC_SOLR_URL="https://semantic.test/solr/catalog/",
    SEMANTIC_SOLR_USERNAME="semantic-user",
    SEMANTIC_SOLR_PASSWORD="semantic-password",
    SOLR_URL="http://legacy.test/solr/",
    SOLR_CORE_CATALOG_NEW="legacy-core",
    SOLR_USERNAME="legacy-user",
    SOLR_PASSWORD="legacy-password",
)
class SemanticSolrTests(SimpleTestCase):
    def test_semantic_settings_override_legacy_settings(self):
        self.assertEqual(get_semantic_solr_url(), "https://semantic.test/solr/catalog")
        self.assertEqual(
            get_semantic_solr_auth(), HTTPBasicAuth("semantic-user", "semantic-password")
        )

    def test_legacy_fallback_when_semantic_settings_are_missing(self):
        with override_settings():
            del settings.SEMANTIC_SOLR_URL
            del settings.SEMANTIC_SOLR_USERNAME
            del settings.SEMANTIC_SOLR_PASSWORD
            self.assertEqual(get_semantic_solr_url(), "http://legacy.test/solr/legacy-core")
            self.assertEqual(get_semantic_solr_auth(), HTTPBasicAuth("legacy-user", "legacy-password"))

    def test_no_credentials_is_supported_without_legacy_settings(self):
        with override_settings():
            del settings.SEMANTIC_SOLR_USERNAME
            del settings.SEMANTIC_SOLR_PASSWORD
            del settings.SOLR_USERNAME
            del settings.SOLR_PASSWORD
            self.assertIsNone(get_semantic_solr_auth())

    @override_settings(SEMANTIC_SOLR_USERNAME="", SEMANTIC_SOLR_PASSWORD="")
    def test_empty_semantic_credentials_disable_legacy_auth(self):
        self.assertIsNone(get_semantic_solr_auth())

    def test_explicit_credentials_override_settings(self):
        self.assertEqual(get_semantic_solr_auth("override", "secret"), HTTPBasicAuth("override", "secret"))
        self.assertIsNone(get_semantic_solr_auth("", ""))

    def test_partial_credentials_are_rejected(self):
        for username, password in (("user", ""), ("", "secret")):
            with self.subTest(username=username), self.assertRaisesMessage(
                ValueError, "Solr authentication requires both a username and a password."
            ):
                get_semantic_solr_auth(username, password)

    def test_both_indexers_use_credentials_for_every_solr_operation(self):
        record = SimpleNamespace(
            published=True,
            reference_code="test-isad",
            archival_reference_code="test-fa",
            archival_unit=SimpleNamespace(isad=SimpleNamespace(published=True)),
        )
        for indexer_class, module_path, loader in (
            (FindingAidsSemanticIndexer, "finding_aids.indexers.finding_aids_semantic_indexer", "_get_finding_aids_record"),
            (ISADSemanticIndexer, "isad.indexers.isad_semantic_indexer", "_get_isad"),
        ):
            for credentials, expected_auth in (
                ({}, HTTPBasicAuth("semantic-user", "semantic-password")),
                ({"solr_username": "override", "solr_password": "secret"}, HTTPBasicAuth("override", "secret")),
                ({"solr_username": "", "solr_password": ""}, None),
            ):
                with self.subTest(indexer=indexer_class.__name__, credentials=credentials), patch.object(
                    indexer_class, loader, return_value=record
                ), patch(module_path + ".pysolr.Solr") as solr_class, patch(
                    module_path + ".post", return_value=Mock(status_code=200, text="ok")
                ) as post, patch.object(indexer_class, "create_solr_document"), patch.object(
                    indexer_class, "_get_solr_id", return_value="doc-1"
                ), patch("builtins.print"):
                    indexer = indexer_class(1, solr_url="https://override.test/solr/catalog/", **credentials)
                    solr_class.assert_called_once_with("https://override.test/solr/catalog", auth=expected_auth)
                    indexer.doc = {"id": "doc-1"}
                    indexer.index()
                    indexer.index_with_requests()
                    indexer.commit()
                    indexer.delete()

                    solr_class.return_value.add.assert_called_once_with([indexer.doc])
                    solr_class.return_value.delete.assert_called_once_with(id="doc-1", commit=True)
                    self.assertEqual(post.call_count, 2)
                    for call in post.call_args_list:
                        self.assertEqual(call.kwargs["auth"], expected_auth)
                        self.assertTrue(call.args[0].startswith("https://override.test/solr/catalog/"))

    def test_indexers_default_to_semantic_url(self):
        with patch("finding_aids.indexers.finding_aids_semantic_indexer.pysolr.Solr") as solr:
            FindingAidsSemanticIndexer(1, load_record=False)
            solr.assert_called_once_with(
                "https://semantic.test/solr/catalog", auth=HTTPBasicAuth("semantic-user", "semantic-password")
            )
        with patch.object(ISADSemanticIndexer, "_get_isad"), patch(
            "isad.indexers.isad_semantic_indexer.pysolr.Solr"
        ) as solr:
            ISADSemanticIndexer(1)
            solr.assert_called_once_with(
                "https://semantic.test/solr/catalog", auth=HTTPBasicAuth("semantic-user", "semantic-password")
            )

    def test_command_overrides_authenticate_both_documents_and_commit(self):
        isad = SimpleNamespace(id=1, published=True, reference_code="test-isad")
        finding_aid = SimpleNamespace(id=2, published=True, archival_reference_code="test-fa")
        command_module = "finding_aids.management.commands.index_semantic_catalog_slice"
        with patch.object(Command, "_get_archival_unit", return_value=SimpleNamespace(isad=isad)), patch.object(
            Command, "_get_series_context", return_value="context"
        ), patch.object(Command, "_get_finding_aids_entities") as entities, patch.object(
            Command, "_build_isad_semantic_text", return_value="isad text"
        ), patch.object(Command, "_build_finding_aids_semantic_text", return_value="fa text"), patch(
            command_module + ".ISADSemanticIndexer"
        ) as isad_indexer, patch(command_module + ".FindingAidsSemanticIndexer") as fa_indexer, patch.object(
            EmbeddingClient, "embed_document", return_value=[0.1, 0.2]
        ), patch(command_module + ".requests.post", return_value=Mock(status_code=200)) as post:
            entities.return_value.iterator.return_value = iter([finding_aid])
            isad_indexer.return_value.doc = {"id": "isad-1"}
            fa_indexer.return_value.doc = {"id": "fa-2"}
            output = StringIO()
            call_command(
                "index_semantic_catalog_slice", "--fonds", "1", "--subfonds", "1", "--series", "1",
                "--solr-url", "https://override.test/solr/catalog/",
                "--solr-username", "override", "--solr-password", "secret", stdout=output,
            )

            self.assertEqual(post.call_count, 3)
            for call in post.call_args_list:
                self.assertEqual(call.kwargs["auth"], HTTPBasicAuth("override", "secret"))
                self.assertTrue(call.args[0].startswith("https://override.test/solr/catalog/"))
            self.assertEqual(post.call_args.kwargs["params"], {"commit": "true"})
            for indexer, record_id in ((isad_indexer, 1), (fa_indexer, 2)):
                indexer.assert_called_once_with(
                    record_id, solr_url="https://override.test/solr/catalog",
                    solr_username="override", solr_password="secret",
                )
            self.assertNotIn("secret", output.getvalue())

    def test_command_defaults_to_configured_auth(self):
        command = Command()
        options = vars(command.create_parser("manage.py", "index_semantic_catalog_slice").parse_args(
            ["--fonds", "1", "--subfonds", "1", "--series", "1"]
        ))
        self.assertEqual(options["solr_url"], "https://semantic.test/solr/catalog/")
        self.assertEqual(command._get_solr_auth(options), HTTPBasicAuth("semantic-user", "semantic-password"))

    def test_command_retains_local_url_default_without_semantic_setting(self):
        with override_settings():
            del settings.SEMANTIC_SOLR_URL
            parser = Command().create_parser("manage.py", "index_semantic_catalog_slice")
            options = parser.parse_args(["--fonds", "1", "--subfonds", "1", "--series", "1"])
        self.assertEqual(options.solr_url, "http://localhost:8983/solr/catalog")

    @override_settings(SEMANTIC_SOLR_USERNAME="", SEMANTIC_SOLR_PASSWORD="")
    def test_command_rejects_partial_auth_before_loading_records(self):
        with patch.object(Command, "_get_archival_unit") as load_record, self.assertRaisesMessage(
            CommandError, "Solr authentication requires both a username and a password."
        ):
            call_command(
                "index_semantic_catalog_slice", fonds=1, subfonds=1, series=1, solr_username="user"
            )
        load_record.assert_not_called()

    @override_settings(SEMANTIC_EMBEDDING_USERNAME="", SEMANTIC_EMBEDDING_PASSWORD="")
    def test_embedding_request_does_not_include_solr_auth(self):
        with patch(
            "finding_aids.management.commands.index_semantic_catalog_slice.requests.post"
        ) as post:
            post.return_value.json.return_value = {"embedding": [0.1, 0.2]}
            self.assertEqual(EmbeddingClient("http://embedding.test", 10).embed_document("text"), [0.1, 0.2])
        self.assertIsNone(post.call_args.kwargs["auth"])
