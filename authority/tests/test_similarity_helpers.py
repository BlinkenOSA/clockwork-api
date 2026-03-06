from django.test import TestCase

from authority.helpers.similarity_helpers import fold, _trigrams, _hash64, simhash64


class SimilarityHelpersTests(TestCase):
    def test_fold_normalizes_accents_and_whitespace(self):
        self.assertEqual(fold(" János Kádár "), "janos kadar")

    def test_fold_handles_none(self):
        self.assertEqual(fold(None), "")

    def test_trigrams_padding(self):
        self.assertEqual(_trigrams("abc"), ["  a", " ab", "abc", "bc ", "c  "])

    def test_hash64_deterministic(self):
        self.assertEqual(_hash64("abc"), _hash64("abc"))

    def test_simhash64_empty_is_deterministic(self):
        value = simhash64("")
        self.assertEqual(value, simhash64(""))
        self.assertGreaterEqual(value, 0)

    def test_simhash64_deterministic(self):
        self.assertEqual(simhash64("test string"), simhash64("test string"))
