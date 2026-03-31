from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import Http404
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from catalog.views.research_request_views.researcher_forgot_card_number import ResearcherForgotCardNumber


class _SerializerStub:
    def __init__(self, validated_data=None, validation_error=None):
        self.validated_data = validated_data or {}
        self._validation_error = validation_error

    def is_valid(self, raise_exception=False):
        if self._validation_error is not None:
            raise self._validation_error
        return True


class ResearcherForgotCardNumberViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ResearcherForgotCardNumber.as_view()

    def _post(self, payload=None):
        return self.view(self.factory.post("/v1/catalog/researcher-card-number/", payload or {}, format="json"))

    def test_post_success_sends_mail_and_returns_201(self):
        serializer = _SerializerStub(validated_data={"email": "user@example.com"})
        researcher = SimpleNamespace(id=1, email="user@example.com")
        mail = SimpleNamespace(send_researcher_forgot_card_number=Mock())

        with patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.ResearcherForgotCardNumberSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.get_object_or_404",
            return_value=researcher,
        ) as mock_get_object_or_404, patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.EmailWithTemplate",
            return_value=mail,
        ) as mock_mail_cls:
            response = self._post({"email": "user@example.com"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, "ok")

        mock_get_object_or_404.assert_called_once()
        mock_mail_cls.assert_called_once_with(
            researcher=researcher,
            context={"researcher": researcher},
        )
        mail.send_researcher_forgot_card_number.assert_called_once()

    def test_post_propagates_not_found(self):
        serializer = _SerializerStub(validated_data={"email": "missing@example.com"})

        with patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.ResearcherForgotCardNumberSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.get_object_or_404",
            side_effect=Http404,
        ):
            response = self._post({"email": "missing@example.com"})

        self.assertEqual(response.status_code, 404)

    def test_post_returns_400_when_serializer_validation_fails(self):
        serializer = _SerializerStub(validation_error=ValidationError({"email": ["invalid"]}))

        with patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.ResearcherForgotCardNumberSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.researcher_forgot_card_number.EmailWithTemplate",
        ) as mock_mail_cls:
            response = self._post({"email": "bad"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"email": ["invalid"]})
        mock_mail_cls.assert_not_called()
