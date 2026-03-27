from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from django.core.exceptions import ObjectDoesNotExist
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from catalog.views.research_request_views.request_views import ResearcherRequestView


class _SerializerStub:
    def __init__(self, is_valid_result, validated_data=None, errors=None):
        self._is_valid_result = is_valid_result
        self.validated_data = validated_data or {}
        self.errors = errors or {}

    def is_valid(self, raise_exception=False):
        return self._is_valid_result


class ResearcherRequestViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ResearcherRequestView.as_view()

    def _post(self, payload=None):
        return self.view(self.factory.post("/v1/catalog/request/", payload or {}, format="json"))

    def test_post_returns_serializer_errors_when_invalid(self):
        serializer = _SerializerStub(False, errors={"items": ["invalid"]})

        with patch(
            "catalog.views.research_request_views.request_views.ResearchRequestSerializer",
            return_value=serializer,
        ):
            response = self._post({"x": 1})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"items": ["invalid"]})

    def test_post_returns_400_when_researcher_not_found(self):
        serializer = _SerializerStub(
            True,
            validated_data={
                "researcher": 99,
                "request_date": "2026-03-06",
                "items": [],
            },
        )

        with patch(
            "catalog.views.research_request_views.request_views.ResearchRequestSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.request_views.Researcher.objects.get",
            side_effect=ObjectDoesNotExist,
        ):
            response = self._post({})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"researcher": "Researcher not found."})

    def test_post_returns_400_for_invalid_container_in_fa_item(self):
        serializer = _SerializerStub(
            True,
            validated_data={
                "researcher": 1,
                "request_date": "2026-03-06",
                "items": [{"origin": "FA", "container": 7, "ams_id": 12}],
                "research_subject": "Subject",
                "motivation": "Motivation",
            },
        )
        researcher = SimpleNamespace(id=1)
        request_obj = SimpleNamespace(id=10)

        with patch(
            "catalog.views.research_request_views.request_views.ResearchRequestSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.request_views.Researcher.objects.get",
            return_value=researcher,
        ), patch(
            "catalog.views.research_request_views.request_views.Request.objects.get_or_create",
            return_value=(request_obj, True),
        ), patch(
            "catalog.views.research_request_views.request_views.Container.objects.get",
            side_effect=ObjectDoesNotExist,
        ):
            response = self._post({})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"container": "Invalid container for requested item."})

    def test_post_returns_400_for_invalid_ams_id_in_fa_item(self):
        serializer = _SerializerStub(
            True,
            validated_data={
                "researcher": 1,
                "request_date": "2026-03-06",
                "items": [{"origin": "FA", "container": 7, "ams_id": 12}],
                "research_subject": "Subject",
                "motivation": "Motivation",
            },
        )
        researcher = SimpleNamespace(id=1)
        request_obj = SimpleNamespace(id=10)
        container = SimpleNamespace(id=7)

        with patch(
            "catalog.views.research_request_views.request_views.ResearchRequestSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.request_views.Researcher.objects.get",
            return_value=researcher,
        ), patch(
            "catalog.views.research_request_views.request_views.Request.objects.get_or_create",
            return_value=(request_obj, True),
        ), patch(
            "catalog.views.research_request_views.request_views.Container.objects.get",
            return_value=container,
        ), patch(
            "catalog.views.research_request_views.request_views.RequestItem.objects.get_or_create",
            return_value=(SimpleNamespace(id=21), True),
        ), patch(
            "catalog.views.research_request_views.request_views.FindingAidsEntity.objects.get",
            side_effect=ObjectDoesNotExist,
        ):
            response = self._post({})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"ams_id": "AMS ID field invalid!"})

    def test_post_success_with_restricted_content_and_mixed_items(self):
        serializer = _SerializerStub(
            True,
            validated_data={
                "researcher": 1,
                "request_date": "2026-03-06",
                "items": [
                    {"origin": "FA", "container": 7, "ams_id": 12},
                    {"origin": "LIB", "title": "Book", "call_number": "CN-1", "ams_id": "A-9"},
                ],
                "research_subject": "My Subject",
                "motivation": "My Motivation",
            },
        )

        researcher = SimpleNamespace(id=1)
        request_obj = SimpleNamespace(id=10)
        container = SimpleNamespace(id=7)
        request_item_fa = SimpleNamespace(id=21)
        request_item_lib = SimpleNamespace(id=22)
        finding_aids_entity = SimpleNamespace(id=12, restricted=True)
        restriction = SimpleNamespace(save=Mock())
        mail = SimpleNamespace(
            send_new_request_admin=Mock(),
            send_new_request_user=Mock(),
            send_new_request_restricted_decision_maker=Mock(),
        )

        with patch(
            "catalog.views.research_request_views.request_views.ResearchRequestSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.request_views.Researcher.objects.get",
            return_value=researcher,
        ), patch(
            "catalog.views.research_request_views.request_views.Request.objects.get_or_create",
            return_value=(request_obj, True),
        ), patch(
            "catalog.views.research_request_views.request_views.Container.objects.get",
            return_value=container,
        ), patch(
            "catalog.views.research_request_views.request_views.RequestItem.objects.get_or_create",
            side_effect=[(request_item_fa, True), (request_item_lib, True)],
        ) as mock_request_item_get_or_create, patch(
            "catalog.views.research_request_views.request_views.FindingAidsEntity.objects.get",
            return_value=finding_aids_entity,
        ), patch(
            "catalog.views.research_request_views.request_views.RequestItemPart.objects.get_or_create",
            return_value=(SimpleNamespace(id=31), True),
        ), patch(
            "catalog.views.research_request_views.request_views.RequestItemRestriction.objects.get_or_create",
            return_value=(restriction, True),
        ), patch(
            "catalog.views.research_request_views.request_views.EmailWithTemplate",
            return_value=mail,
        ) as mock_mail_cls:
            response = self._post({})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ok")

        self.assertEqual(mock_request_item_get_or_create.call_count, 2)
        self.assertEqual(
            mock_request_item_get_or_create.call_args_list,
            [
                call(request=request_obj, item_origin="FA", container=container),
                call(
                    request=request_obj,
                    item_origin="LIB",
                    title="Book",
                    identifier="CN-1",
                    library_id="A-9",
                    quantity="",
                ),
            ],
        )

        self.assertEqual(restriction.research_subject, "My Subject")
        self.assertEqual(restriction.motivation, "My Motivation")
        restriction.save.assert_called_once()

        mock_mail_cls.assert_called_once()
        mail.send_new_request_admin.assert_called_once()
        mail.send_new_request_user.assert_called_once()
        mail.send_new_request_restricted_decision_maker.assert_called_once()

    def test_post_success_without_restricted_content_does_not_send_restricted_mail(self):
        serializer = _SerializerStub(
            True,
            validated_data={
                "researcher": 1,
                "request_date": "2026-03-06",
                "items": [{"origin": "LIB", "title": "Film", "call_number": "CN-2", "ams_id": "A-10", "volume": "2"}],
            },
        )

        researcher = SimpleNamespace(id=1)
        request_obj = SimpleNamespace(id=10)
        mail = SimpleNamespace(
            send_new_request_admin=Mock(),
            send_new_request_user=Mock(),
            send_new_request_restricted_decision_maker=Mock(),
        )

        with patch(
            "catalog.views.research_request_views.request_views.ResearchRequestSerializer",
            return_value=serializer,
        ), patch(
            "catalog.views.research_request_views.request_views.Researcher.objects.get",
            return_value=researcher,
        ), patch(
            "catalog.views.research_request_views.request_views.Request.objects.get_or_create",
            return_value=(request_obj, True),
        ), patch(
            "catalog.views.research_request_views.request_views.RequestItem.objects.get_or_create",
            return_value=(SimpleNamespace(id=22), True),
        ) as mock_request_item_get_or_create, patch(
            "catalog.views.research_request_views.request_views.EmailWithTemplate",
            return_value=mail,
        ):
            response = self._post({})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ok")

        mock_request_item_get_or_create.assert_called_once_with(
            request=request_obj,
            item_origin="LIB",
            title="Film",
            identifier="CN-2",
            library_id="A-10",
            quantity="2",
        )
        mail.send_new_request_admin.assert_called_once()
        mail.send_new_request_user.assert_called_once()
        mail.send_new_request_restricted_decision_maker.assert_not_called()
