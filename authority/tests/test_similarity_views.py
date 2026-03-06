from types import SimpleNamespace
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.reverse import reverse

from authority.views.similarity_views import person_similarity_views
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class _FakePerson:
    def __init__(self, person_id, first_name, last_name, **extra):
        self.id = person_id
        self.first_name = first_name
        self.last_name = last_name
        self.wikidata_id = extra.get("wikidata_id")
        self.wiki_url = extra.get("wiki_url")
        self.authority_url = extra.get("authority_url")
        self.other_url = extra.get("other_url")
        self.similarity_percent = extra.get("similarity_percent")
        self.deleted = False

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def delete(self):
        self.deleted = True


class PersonSimilarityViewsTests(TestViewsBaseClass):
    def setUp(self):
        self.init()

    def test_person_similar_by_id_not_found(self):
        with patch(
            "authority.views.similarity_views.person_similarity_views.Person.objects.get",
            side_effect=person_similarity_views.Person.DoesNotExist,
        ):
            response = self.client.get(reverse("authority-v1:person-similar-by-id", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Not found."})

    def test_person_similar_by_id_returns_serialized_results(self):
        target = _FakePerson(11, "John", "Smith")
        match = _FakePerson(
            22,
            "Jon",
            "Smythe",
            wikidata_id="Q123",
            wiki_url="https://example.com/wiki/jon",
            authority_url="https://example.com/authority/jon",
            other_url="https://example.com/other/jon",
            similarity_percent=91,
        )

        with patch(
            "authority.views.similarity_views.person_similarity_views.Person.objects.get",
            return_value=target,
        ), patch(
            "authority.views.similarity_views.person_similarity_views.similar_people",
            return_value=[match],
        ) as mock_similar_people:
            response = self.client.get(
                reverse("authority-v1:person-similar-by-id", args=[target.id]),
                {
                    "limit": "7",
                    "min_similarity": "0.3",
                    "max_candidates": "123",
                    "max_hamming": "4",
                },
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], match.id)
        self.assertEqual(response.data[0]["name"], "Smythe, Jon")
        self.assertEqual(response.data[0]["similarity_percent"], 91)

        mock_similar_people.assert_called_once_with(
            "John Smith",
            exclude_id=target.id,
            limit=7,
            min_similarity=0.3,
            max_candidates=123,
            max_hamming=4,
        )

    def test_person_similar_merge_requires_ids(self):
        response = self.client.post(reverse("authority-v1:person-merge"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "keep_id and merge_id are required."})

    def test_person_similar_merge_requires_different_ids(self):
        response = self.client.post(
            reverse("authority-v1:person-merge"),
            {"keep_id": 1, "merge_id": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "keep_id and merge_id must be different."})

    def test_person_similar_merge_not_found(self):
        with patch(
            "authority.views.similarity_views.person_similarity_views.Person.objects.get",
            side_effect=person_similarity_views.Person.DoesNotExist,
        ):
            response = self.client.post(
                reverse("authority-v1:person-merge"),
                {"keep_id": 1, "merge_id": 2},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "One or both persons not found."})

    def test_person_similar_merge_handles_unexpected_error(self):
        with patch(
            "authority.views.similarity_views.person_similarity_views.Person.objects.get",
            side_effect=RuntimeError("boom"),
        ):
            response = self.client.post(
                reverse("authority-v1:person-merge"),
                {"keep_id": 1, "merge_id": 2},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Unexpected error: boom"})

    def test_person_similar_merge_success(self):
        keep = _FakePerson(1, "John", "Smith")
        merge = _FakePerson(2, "Jon", "Smythe")

        subject_person_manager = Mock()
        entity = SimpleNamespace(subject_person=subject_person_manager)
        associated_qs = Mock()

        with patch(
            "authority.views.similarity_views.person_similarity_views.Person.objects.get",
            side_effect=[keep, merge],
        ), patch(
            "authority.views.similarity_views.person_similarity_views.FindingAidsEntity.objects.filter",
            return_value=[entity],
        ), patch(
            "authority.views.similarity_views.person_similarity_views.FindingAidsEntityAssociatedPerson.objects.filter",
            return_value=associated_qs,
        ):
            response = self.client.post(
                reverse("authority-v1:person-merge"),
                {"keep_id": keep.id, "merge_id": merge.id},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "message": "Merge completed successfully.",
                "keep_id": keep.id,
                "deleted_merge_id": merge.id,
            },
        )

        subject_person_manager.add.assert_called_once_with(keep)
        subject_person_manager.remove.assert_called_once_with(merge)
        associated_qs.update.assert_called_once_with(associated_person=keep)
        self.assertTrue(merge.deleted)
