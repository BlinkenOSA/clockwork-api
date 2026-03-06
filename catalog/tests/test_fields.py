from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError

from catalog.serializer_fields.hcaptcha_field import HCaptchaField
from catalog.serializer_fields.origin_field import OriginField


class OriginFieldTests(TestCase):
    def test_origin_mapping(self):
        field = OriginField()
        self.assertEqual(field.to_internal_value("Archives"), "FA")
        self.assertEqual(field.to_internal_value("Library"), "L")
        self.assertEqual(field.to_internal_value("Film Library"), "FL")

    def test_origin_invalid(self):
        field = OriginField()
        with self.assertRaises(ValidationError):
            field.to_internal_value("Unknown")


class HCaptchaFieldTests(TestCase):
    @override_settings(HCAPTCHA_VERIFY_URL="https://hcaptcha.example/verify", HCAPTCHA_SITE_KEY="secret")
    def test_hcaptcha_success(self):
        field = HCaptchaField()
        response = Mock(status_code=200)
        response.json.return_value = {"success": True}
        with patch("catalog.serializer_fields.hcaptcha_field.post", return_value=response):
            self.assertEqual(field.to_internal_value("token"), "")

    @override_settings(HCAPTCHA_VERIFY_URL="https://hcaptcha.example/verify", HCAPTCHA_SITE_KEY="secret")
    def test_hcaptcha_failure(self):
        field = HCaptchaField()
        response = Mock(status_code=200)
        response.json.return_value = {"success": False}
        with patch("catalog.serializer_fields.hcaptcha_field.post", return_value=response):
            with self.assertRaises(ValidationError):
                field.to_internal_value("token")

    def test_hcaptcha_missing_token(self):
        field = HCaptchaField()
        with self.assertRaises(ValidationError):
            field.to_internal_value("")
