from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from clockwork_api.services.ark import create_ark_for_record, ensure_ark


class ArkServiceTests(SimpleTestCase):
    @override_settings(
        ARK_API_TOKEN="secret",
        ARK_NAAN=12345,
        ARK_SHOULDER="/x1",
        ARK_COMMITMENT="test-commitment",
        CATALOG_URL="https://catalog.archivum.org/catalog",
    )
    @patch("clockwork_api.services.ark.post")
    def test_create_ark_for_record_uses_arklet_payload(self, mock_post):
        response = Mock()
        response.content = b'{"ark":"ark:/12345/x1abc"}'
        response.json.return_value = {"ark": "ark:/12345/x1abc"}
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        ark = create_ark_for_record(
            record_type="isad",
            record_id=7,
            catalog_id="abc123",
            reference_code="HU OSA 1"
        )

        self.assertEqual(ark, "ark:/12345/x1abc")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer secret"})
        self.assertEqual(kwargs["json"]["naan"], 12345)
        self.assertEqual(kwargs["json"]["shoulder"], "/x1")
        self.assertEqual(kwargs["json"]["url"], "https://catalog.archivum.org/catalog/abc123")

    def test_ensure_ark_returns_existing_ark(self):
        instance = SimpleNamespace(ark="ark:/12345/existing", published=True)
        self.assertEqual(ensure_ark(instance, save=False), "ark:/12345/existing")

    def test_ensure_ark_skips_unpublished_records(self):
        instance = SimpleNamespace(ark=None, published=False)
        self.assertIsNone(ensure_ark(instance, save=False))
