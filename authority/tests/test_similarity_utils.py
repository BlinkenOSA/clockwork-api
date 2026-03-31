from django.test import TestCase

from authority.similarity import (
    normalize_for_match,
    first_token,
    last_token,
    _initials_boost,
    _mononym_boost,
)


class SimilarityUtilsTests(TestCase):
    def test_normalize_for_match(self):
        self.assertEqual(normalize_for_match(" John,  Smith "), "john smith")

    def test_first_and_last_token(self):
        self.assertEqual(first_token("john smith"), "john")
        self.assertEqual(last_token("john smith"), "smith")
        self.assertEqual(first_token(""), "")
        self.assertEqual(last_token(""), "")

    def test_initials_boost(self):
        self.assertEqual(_initials_boost("j smith", "john smith"), 8)
        self.assertEqual(_initials_boost("john smith", "john smith"), 0)

    def test_mononym_boost(self):
        self.assertEqual(_mononym_boost("john", "john smith"), 16)
        self.assertEqual(_mononym_boost("smi", "john smith"), 6)
