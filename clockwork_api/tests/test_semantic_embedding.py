import json
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import requests
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings
from requests.auth import HTTPBasicAuth

from finding_aids.management.commands.index_semantic_catalog_slice import Command, EmbeddingClient


COMMAND_MODULE = "finding_aids.management.commands.index_semantic_catalog_slice"


def embedding_response(status=200, payload=None):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps({"embedding": [0.1, 0.2]} if payload is None else payload).encode()
    response._content_consumed = True
    return response


@override_settings(
    SEMANTIC_EMBEDDING_BASE_URL="https://embedding.test/embedder/",
    SEMANTIC_EMBEDDING_USERNAME="embedding-user",
    SEMANTIC_EMBEDDING_PASSWORD="embedding-password",
    SEMANTIC_SOLR_URL="https://solr.test/solr/catalog",
    SEMANTIC_SOLR_USERNAME="solr-user",
    SEMANTIC_SOLR_PASSWORD="solr-password",
    SEMANTIC_EMBEDDING_MAX_RETRIES=5,
    SEMANTIC_EMBEDDING_RETRY_DELAY=60,
)
class SemanticEmbeddingTests(SimpleTestCase):
    def test_parser_defaults_to_configured_base_url(self):
        options = Command().create_parser("manage.py", "index_semantic_catalog_slice").parse_args(
            ["--fonds", "1", "--subfonds", "1", "--series", "1"]
        )
        self.assertEqual(options.embedding_base_url, "https://embedding.test/embedder/")
        self.assertEqual(options.embedding_max_retries, 5)
        self.assertEqual(options.embedding_retry_delay, 60)

    @override_settings(SEMANTIC_EMBEDDING_MAX_RETRIES=7, SEMANTIC_EMBEDDING_RETRY_DELAY=120)
    def test_embedding_retry_settings_and_flags(self):
        parser = Command().create_parser("manage.py", "index_semantic_catalog_slice")
        defaults = parser.parse_args(["--all"])
        self.assertEqual((defaults.embedding_max_retries, defaults.embedding_retry_delay), (7, 120))
        client = EmbeddingClient("https://embedding.test", 30)
        self.assertEqual((client.max_retries, client.retry_delay), (7, 120))
        overrides = parser.parse_args(["--all", "--embedding-max-retries", "0", "--embedding-retry-delay", "90"])
        self.assertEqual((overrides.embedding_max_retries, overrides.embedding_retry_delay), (0, 90))

    def test_invalid_retry_options_fail_before_loading_or_sending_records(self):
        for options, message in (
            ({"embedding_max_retries": -1}, "--embedding-max-retries must be zero or greater."),
            ({"embedding_retry_delay": 0}, "--embedding-retry-delay must be greater than zero."),
            ({"embedding_retry_delay": -1}, "--embedding-retry-delay must be greater than zero."),
        ):
            with self.subTest(options=options), patch.object(Command, "_get_archival_units") as load, patch(
                COMMAND_MODULE + ".requests.post",
            ) as post, self.assertRaisesMessage(CommandError, message):
                call_command("index_semantic_catalog_slice", all=True, **options)
            load.assert_not_called()
            post.assert_not_called()

    def test_transient_failures_wait_a_minute_and_retry_the_same_embedding(self):
        for failure in (
            *(embedding_response(status) for status in (408, 429, 500, 502, 503, 504)),
            requests.exceptions.ReadTimeout(), requests.exceptions.ConnectTimeout(), requests.exceptions.ConnectionError(),
        ):
            with self.subTest(failure=failure), patch(
                COMMAND_MODULE + ".requests.post", side_effect=[failure, embedding_response()],
            ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
                messages = []
                client = EmbeddingClient("https://embedding.test/embedder/", 30, retry_logger=messages.append)
                self.assertEqual(client.embed_document("record text", document_id="fa-2"), [0.1, 0.2])
                self.assertEqual(post.call_count, 2)
                self.assertEqual(post.call_args_list[0], post.call_args_list[1])
                self.assertEqual(post.call_args.kwargs["json"], {"text": "record text", "type": "document"})
                self.assertEqual(post.call_args.kwargs["auth"], HTTPBasicAuth("embedding-user", "embedding-password"))
                sleep.assert_called_once_with(60)
                self.assertEqual(len(messages), 1)
                self.assertIn("for document fa-2 failed", messages[0])
                self.assertIn("retry 1/5 in 60s", messages[0])
                self.assertNotIn("record text", messages[0])
                self.assertNotIn("embedding-password", messages[0])

    def test_permanent_http_errors_fail_without_waiting(self):
        for status in (400, 401, 403, 404, 422):
            with self.subTest(status=status), patch(
                COMMAND_MODULE + ".requests.post", return_value=embedding_response(status),
            ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
                with self.assertRaises(requests.exceptions.HTTPError):
                    EmbeddingClient("https://embedding.test", 30).embed_document("text")
                post.assert_called_once()
                sleep.assert_not_called()

    def test_exhausted_timeouts_report_the_document_without_retrying_forever(self):
        failure = requests.exceptions.ReadTimeout()
        with patch(COMMAND_MODULE + ".requests.post", side_effect=failure) as post, patch(
            COMMAND_MODULE + ".time.sleep",
        ) as sleep:
            client = EmbeddingClient("https://embedding.test", 30, max_retries=2, retry_delay=120, retry_logger=Mock())
            with self.assertRaisesMessage(
                CommandError, "Embedding request for document fa-2 failed after 3 attempt(s): ReadTimeout",
            ) as error:
                client.embed_document("text", document_id="fa-2")
            self.assertIs(error.exception.__cause__, failure)
            self.assertEqual(post.call_count, 3)
            self.assertEqual(sleep.call_args_list, [call(120), call(120)])

    def test_embedding_retries_can_be_disabled(self):
        with patch(COMMAND_MODULE + ".requests.post", return_value=embedding_response(502)) as post, patch(
            COMMAND_MODULE + ".time.sleep",
        ) as sleep:
            with self.assertRaisesMessage(CommandError, "failed after 1 attempt(s): HTTP 502"):
                EmbeddingClient("https://embedding.test", 30, max_retries=0).embed_document("text")
            post.assert_called_once()
            sleep.assert_not_called()

    def test_invalid_embedding_payload_is_not_retried(self):
        malformed = embedding_response()
        malformed._content = b"not JSON"
        for response, error in (
            (embedding_response(payload={}), ValueError),
            (malformed, requests.exceptions.JSONDecodeError),
        ):
            with self.subTest(response=response), patch(
                COMMAND_MODULE + ".requests.post", return_value=response,
            ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
                with self.assertRaises(error):
                    EmbeddingClient("https://embedding.test", 30).embed_document("text")
                post.assert_called_once()
                sleep.assert_not_called()

    def test_command_recovers_from_502_and_indexes_following_records(self):
        records = [SimpleNamespace(id=number, published=True, archival_reference_code="FA %s" % number) for number in (2, 3)]
        with patch.object(Command, "_get_archival_units") as units, patch.object(
            Command, "_get_series_context", return_value="context",
        ), patch.object(Command, "_get_finding_aids_entities") as entities, patch.object(
            Command, "_build_finding_aids_semantic_text", return_value="record text",
        ), patch(COMMAND_MODULE + ".FindingAidsSemanticIndexer") as indexer, patch(
            COMMAND_MODULE + ".requests.post",
            side_effect=[embedding_response(502), embedding_response(502), embedding_response(), Mock(status_code=200),
                         embedding_response(), Mock(status_code=200), Mock(status_code=200)],
        ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
            units.return_value.iterator.return_value = iter([SimpleNamespace()])
            entities.return_value.iterator.return_value = iter(records)
            indexer.side_effect = [Mock(doc={"id": "fa-2"}), Mock(doc={"id": "fa-3"})]
            output, errors = StringIO(), StringIO()
            call_command(
                "index_semantic_catalog_slice", all=True, embedding_max_retries=2, embedding_retry_delay=120,
                stdout=output, stderr=errors,
            )
            self.assertEqual(post.call_count, 7)
            self.assertEqual(sleep.call_args_list, [call(120), call(120)])
            self.assertIn("document fa-2 failed (HTTP 502); retry 1/2 in 120s", errors.getvalue())
            self.assertIn("document fa-2 failed (HTTP 502); retry 2/2 in 120s", errors.getvalue())
            self.assertEqual(post.call_args_list[3].kwargs["json"], {"id": "fa-2", "semantic_vector": [0.1, 0.2]})
            self.assertEqual(post.call_args_list[5].kwargs["json"], {"id": "fa-3", "semantic_vector": [0.1, 0.2]})
            self.assertEqual(post.call_args.kwargs["params"], {"commit": "true"})
            self.assertIn("Processed 2 document(s).", output.getvalue())

    def test_exhausted_502_retries_do_not_send_an_incomplete_document_or_commit(self):
        record = SimpleNamespace(id=2, published=True, archival_reference_code="FA 2")
        with patch.object(Command, "_get_archival_units") as units, patch.object(
            Command, "_get_series_context", return_value="context",
        ), patch.object(Command, "_get_finding_aids_entities") as entities, patch.object(
            Command, "_build_finding_aids_semantic_text", return_value="record text",
        ), patch(COMMAND_MODULE + ".FindingAidsSemanticIndexer") as indexer, patch(
            COMMAND_MODULE + ".requests.post", side_effect=[embedding_response(502), embedding_response(502)],
        ) as post, patch(COMMAND_MODULE + ".time.sleep") as sleep:
            units.return_value.iterator.return_value = iter([SimpleNamespace()])
            entities.return_value.iterator.return_value = iter([record])
            indexer.return_value.doc = {"id": "fa-2"}
            output, errors = StringIO(), StringIO()
            with self.assertRaisesMessage(CommandError, "document fa-2 failed after 2 attempt(s): HTTP 502"):
                call_command(
                    "index_semantic_catalog_slice", all=True, embedding_max_retries=1,
                    stdout=output, stderr=errors,
                )
            self.assertEqual(post.call_count, 2)
            self.assertTrue(all(request.args[0].endswith("/embed") for request in post.call_args_list))
            sleep.assert_called_once_with(60)
            self.assertNotIn("Processed", output.getvalue())

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
