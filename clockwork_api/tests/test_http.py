from django.test import TestCase
from unittest.mock import patch

import clockwork_api.http as http


class HttpTimeoutTests(TestCase):
    def test_get_applies_default_timeout(self):
        with patch.object(http, "DEFAULT_TIMEOUT", 7):
            with patch("clockwork_api.http.requests.request") as req:
                http.get("http://example.com")
                _, kwargs = req.call_args
                self.assertEqual(kwargs["timeout"], 7)

    def test_get_preserves_explicit_timeout(self):
        with patch.object(http, "DEFAULT_TIMEOUT", 7):
            with patch("clockwork_api.http.requests.request") as req:
                http.get("http://example.com", timeout=2)
                _, kwargs = req.call_args
                self.assertEqual(kwargs["timeout"], 2)

    def test_session_request_applies_default_timeout(self):
        with patch.object(http, "DEFAULT_TIMEOUT", 9):
            with patch("requests.Session.request") as req:
                session = http.Session()
                session.request("GET", "http://example.com")
                _, kwargs = req.call_args
                self.assertEqual(kwargs["timeout"], 9)
