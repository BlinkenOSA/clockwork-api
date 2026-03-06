from unittest.mock import patch

from django.test import TestCase

from catalog.serializers.research_request_serializer import ResearchRequestSerializer
from catalog.serializers.researcher_forgot_card_number_serializer import ResearcherForgotCardNumberSerializer
from catalog.serializers.researcher_serializer import ResearcherSerializer
from research.models import Researcher


class ResearcherForgotCardNumberSerializerTests(TestCase):
    def test_email_mismatch(self):
        with patch("catalog.serializer_fields.hcaptcha_field.HCaptchaField.to_internal_value", return_value=""):
            serializer = ResearcherForgotCardNumberSerializer(data={
                "email": "a@example.com",
                "email_confirm": "b@example.com",
                "captcha": "token",
            })
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_email_match(self):
        with patch("catalog.serializer_fields.hcaptcha_field.HCaptchaField.to_internal_value", return_value=""):
            serializer = ResearcherForgotCardNumberSerializer(data={
                "email": "a@example.com",
                "email_confirm": "a@example.com",
                "captcha": "token",
            })
            self.assertTrue(serializer.is_valid(), serializer.errors)


class ResearcherSerializerTests(TestCase):
    def test_researcher_serializer_valid(self):
        with patch("catalog.serializer_fields.hcaptcha_field.HCaptchaField.to_internal_value", return_value=""):
            serializer = ResearcherSerializer(data={
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "country": None,
                "city_abroad": "",
                "address_abroad": "",
                "house_number": "",
                "occupation": "ceu",
                "department": "",
                "degree": None,
                "employer_or_school": "",
                "research_subject": "",
                "captcha": "token",
            })
            self.assertTrue(serializer.is_valid(), serializer.errors)


class ResearchRequestSerializerTests(TestCase):
    def _base_payload(self, researcher):
        return {
            "card_number": str(researcher.card_number),
            "email": researcher.email,
            "request_date": "2020-01-01",
            "items": [
                {
                    "id": "1",
                    "origin": "Library",
                    "title": "Test item",
                    "call_number": "CN-1",
                    "ams_id": "",
                    "volume": "",
                }
            ],
            "captcha": "token",
        }

    def test_valid_request_for_approved_researcher(self):
        researcher = Researcher.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            status="approved",
        )
        with patch("catalog.serializer_fields.hcaptcha_field.HCaptchaField.to_internal_value", return_value=""):
            serializer = ResearchRequestSerializer(data=self._base_payload(researcher))
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertEqual(serializer.validated_data["researcher"], researcher.id)

    def test_request_rejected_for_new_researcher(self):
        researcher = Researcher.objects.create(
            first_name="New",
            last_name="User",
            email="new@example.com",
            status="new",
        )
        with patch("catalog.serializer_fields.hcaptcha_field.HCaptchaField.to_internal_value", return_value=""):
            serializer = ResearchRequestSerializer(data=self._base_payload(researcher))
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)
