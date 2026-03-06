import builtins
import re
import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from authority import similarity


class _FakeQuerySet:
    def __init__(self, rows, manager):
        self.rows = list(rows)
        self.manager = manager

    def all(self):
        return _FakeQuerySet(self.rows, self.manager)

    def exclude(self, **kwargs):
        rows = self.rows
        if "id" in kwargs:
            rows = [row for row in rows if row["id"] != kwargs["id"]]
        return _FakeQuerySet(rows, self.manager)

    def filter(self, **kwargs):
        rows = self.rows
        if "full_name_folded__regex" in kwargs:
            pattern = re.compile(kwargs["full_name_folded__regex"])
            rows = [row for row in rows if pattern.search(row.get("full_name_folded", ""))]
        if "first_name__istartswith" in kwargs:
            prefix = kwargs["first_name__istartswith"].lower()
            rows = [row for row in rows if row.get("first_name", "").lower().startswith(prefix)]
        if "last_name__istartswith" in kwargs:
            prefix = kwargs["last_name__istartswith"].lower()
            rows = [row for row in rows if row.get("last_name", "").lower().startswith(prefix)]
        if "_dist__lte" in kwargs:
            max_dist = kwargs["_dist__lte"]
            rows = [row for row in rows if row.get("_dist", 0) <= max_dist]
        return _FakeQuerySet(rows, self.manager)

    def annotate(self, **kwargs):
        rows = [dict(row) for row in self.rows]
        if "_full" in kwargs:
            for row in rows:
                row["_full"] = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip().lower()
        return _FakeQuerySet(rows, self.manager)

    def distinct(self):
        seen = set()
        out = []
        for row in self.rows:
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            out.append(row)
        return _FakeQuerySet(out, self.manager)

    def values(self, *fields):
        return [{field: row.get(field) for field in fields} for row in self.rows]

    def none(self):
        return _FakeQuerySet([], self.manager)

    def __or__(self, other):
        return _FakeQuerySet(self.rows + other.rows, self.manager)


class _FakeManager:
    def __init__(self, rows):
        self.rows = list(rows)
        self.people_by_id = {
            row["id"]: SimpleNamespace(
                id=row["id"],
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
            )
            for row in self.rows
        }

    def all(self):
        return _FakeQuerySet(self.rows, self)

    def filter(self, **kwargs):
        if "id__in" in kwargs:
            return [self.people_by_id[idx] for idx in kwargs["id__in"] if idx in self.people_by_id]
        return _FakeQuerySet(self.rows, self).filter(**kwargs)

    def none(self):
        return _FakeQuerySet([], self)


class SimilarPeopleTests(TestCase):
    def _patch_person(self, rows):
        manager = _FakeManager(rows)
        fake_person_model = SimpleNamespace(objects=manager)
        return patch.object(similarity, "Person", fake_person_model)

    def test_similar_people_blank_target_returns_empty(self):
        with self._patch_person([]):
            self.assertEqual(similarity.similar_people(""), [])

    def test_similar_people_single_token_branch(self):
        rows = [
            {"id": 1, "first_name": "John", "last_name": "Smith", "full_name_folded": "john smith"},
            {"id": 2, "first_name": "Alice", "last_name": "Jones", "full_name_folded": "alice jones"},
        ]

        with self._patch_person(rows), patch.object(similarity.fuzz, "WRatio", side_effect=[70, 10]), patch.object(
            similarity.fuzz,
            "partial_ratio",
            side_effect=[60, 10],
        ):
            result = similarity.similar_people("J", min_similarity=0.2, limit=10)

        self.assertEqual([person.id for person in result], [1])
        self.assertEqual(result[0].similarity_percent, 76)

    def test_similar_people_multi_token_branch_with_tfidf(self):
        rows = [
            {
                "id": 1,
                "first_name": "John",
                "last_name": "Smith",
                "full_name_folded": "john smith",
                "_dist": 1,
            },
            {
                "id": 2,
                "first_name": "Jane",
                "last_name": "Doe",
                "full_name_folded": "jane doe",
                "_dist": 1,
            },
        ]

        sklearn_pkg = types.ModuleType("sklearn")
        sklearn_feature = types.ModuleType("sklearn.feature_extraction")
        sklearn_feature_text = types.ModuleType("sklearn.feature_extraction.text")
        sklearn_metrics = types.ModuleType("sklearn.metrics")
        sklearn_pairwise = types.ModuleType("sklearn.metrics.pairwise")

        class _FakeVectorizer:
            def __init__(self, *args, **kwargs):
                pass

            def fit_transform(self, docs):
                return docs

        sklearn_feature_text.TfidfVectorizer = _FakeVectorizer
        sklearn_pairwise.cosine_similarity = lambda a, b: [[0.5, 0.1]]

        fake_modules = {
            "sklearn": sklearn_pkg,
            "sklearn.feature_extraction": sklearn_feature,
            "sklearn.feature_extraction.text": sklearn_feature_text,
            "sklearn.metrics": sklearn_metrics,
            "sklearn.metrics.pairwise": sklearn_pairwise,
        }

        with self._patch_person(rows), patch.dict(sys.modules, fake_modules), patch.object(
            similarity.fuzz,
            "WRatio",
            side_effect=[60, 10],
        ), patch.object(similarity.fuzz, "partial_ratio", side_effect=[60, 10]):
            result = similarity.similar_people("J Smith", min_similarity=0.2, limit=10)

        self.assertEqual([person.id for person in result], [1])
        self.assertEqual(result[0].similarity_percent, 66)

    def test_similar_people_multi_token_falls_back_when_sklearn_unavailable(self):
        rows = [
            {
                "id": 1,
                "first_name": "John",
                "last_name": "Smith",
                "full_name_folded": "john smith",
                "_dist": 1,
            },
        ]

        original_import = builtins.__import__

        def _import_without_sklearn(name, *args, **kwargs):
            if name.startswith("sklearn"):
                raise ImportError("sklearn not installed")
            return original_import(name, *args, **kwargs)

        with self._patch_person(rows), patch("builtins.__import__", side_effect=_import_without_sklearn), patch.object(
            similarity.fuzz,
            "WRatio",
            return_value=100,
        ), patch.object(similarity.fuzz, "partial_ratio", return_value=100):
            result = similarity.similar_people("John Smith", min_similarity=0.2, limit=10)

        self.assertEqual([person.id for person in result], [1])
        self.assertEqual(result[0].similarity_percent, 48)
