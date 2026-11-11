from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings
from requests.auth import HTTPBasicAuth

from finding_aids.management.commands.index_semantic_catalog_slice import Command, EmbeddingClient


COMMAND_MODULE = "finding_aids.management.commands.index_semantic_catalog_slice"


@override_settings(
    SEMANTIC_EMBEDDING_BASE_URL="https://embedding.test/embedder/",
    SEMANTIC_EMBEDDING_USERNAME="embedding-user",
    SEMANTIC_EMBEDDING_PASSWORD="embedding-password",
    SEMANTIC_SOLR_URL="https://solr.test/solr/catalog",
    SEMANTIC_SOLR_USERNAME="solr-user",
    SEMANTIC_SOLR_PASSWORD="solr-password",
)
class SemanticEmbeddingTests(SimpleTestCase):
    def test_parser_defaults_to_configured_base_url(self):
        options = Command().create_parser("manage.py", "index_semantic_catalog_slice").parse_args(
            ["--fonds", "1", "--subfonds", "1", "--series", "1"]
        )
        self.assertEqual(options.embedding_base_url, "https://embedding.test/embedder/")

    def test_client_preserves_proxy_subpath_and_uses_embedding_credentials(self):
        with patch(COMMAND_MODULE + ".requests.post") as post:
            post.return_value.json.return_value = {"embedding": [0.1, 0.2]}
            vector = EmbeddingClient("https://embedding.test/embedder/", 60).embed_document("record text")
        self.assertEqual(vector, [0.1, 0.2])
        post.assert_called_once_with(
            "https://embedding.test/embedder/embed",
            json={"text": "record text", "type": "document"},
            timeout=60,
            auth=HTTPBasicAuth("embedding-user", "embedding-password"),
        )

    def test_explicit_credentials_override_settings_and_empty_pair_disables_auth(self):
        client = EmbeddingClient("https://embedding.test", 30, username="override", password="secret")
        self.assertEqual(client.auth, HTTPBasicAuth("override", "secret"))
        self.assertIsNone(EmbeddingClient("http://localhost:8000", 30, username="", password="").auth)

    def test_partial_credentials_are_rejected_before_loading_records(self):
        for username, password in (("user", ""), ("", "password")):
            with self.subTest(username=username), patch.object(Command, "_get_archival_units") as load:
                with self.assertRaisesMessage(
                    CommandError, "Embedding service authentication requires both a username and a password.",
                ):
                    call_command(
                        "index_semantic_catalog_slice", fonds=1, subfonds=1, series=1,
                        embedding_username=username, embedding_password=password,
                    )
                load.assert_not_called()

    def test_command_keeps_embedding_and_solr_credentials_separate(self):
        record = SimpleNamespace(id=2, published=True, archival_reference_code="test-fa")
        for overrides, expected_url, expected_auth in (
            ({}, "https://embedding.test/embedder/embed", HTTPBasicAuth("embedding-user", "embedding-password")),
            ({"embedding_base_url": "https://override.test/tools/", "embedding_username": "override", "embedding_password": "secret"},
             "https://override.test/tools/embed", HTTPBasicAuth("override", "secret")),
        ):
            with self.subTest(overrides=overrides), patch.object(
                Command, "_get_archival_units",
            ) as units, patch.object(Command, "_get_series_context", return_value="context"), patch.object(
                Command, "_get_finding_aids_entities",
            ) as entities, patch.object(
                Command, "_build_finding_aids_semantic_text", return_value="record text",
            ), patch(COMMAND_MODULE + ".FindingAidsSemanticIndexer") as indexer, patch(
                COMMAND_MODULE + ".requests.post", return_value=Mock(status_code=200),
            ) as post:
                units.return_value.iterator.return_value = iter([SimpleNamespace()])
                entities.return_value.iterator.return_value = iter([record])
                indexer.return_value.doc = {"id": "fa-2"}
                post.return_value.json.return_value = {"embedding": [0.1, 0.2]}
                output = StringIO()
                call_command("index_semantic_catalog_slice", fonds=1, subfonds=1, series=1, stdout=output, **overrides)
                self.assertEqual(post.call_count, 3)
                embedding, document, commit = post.call_args_list
                self.assertEqual(embedding.args[0], expected_url)
                self.assertEqual(embedding.kwargs["auth"], expected_auth)
                self.assertEqual(document.kwargs["auth"], HTTPBasicAuth("solr-user", "solr-password"))
                self.assertEqual(commit.kwargs["auth"], HTTPBasicAuth("solr-user", "solr-password"))
                self.assertEqual(document.kwargs["json"]["semantic_vector"], [0.1, 0.2])
                for secret in ("embedding-password", "solr-password", "secret"):
                    self.assertNotIn(secret, output.getvalue())
