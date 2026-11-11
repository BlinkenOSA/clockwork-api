import os
from unittest import skipUnless

from django.test import SimpleTestCase, tag

from authority.views.lcsh_views import LCSHMixin


@skipUnless(os.environ.get('RUN_LCSH_LIVE_TESTS') == '1', 'Live LoC checks are opt-in')
@tag('external')
class LCSHLiveTests(SimpleTestCase):
    """Optional contract checks against the live Library of Congress service."""

    def test_get_genre(self):
        records = LCSHMixin().get_lcshlinks('Horror', 'genre')
        self.assertIn(
            'http://id.loc.gov/authorities/genreForms/gf2011026321',
            [record['lcsh_id'] for record in records],
            records,
        )

    def test_get_subject(self):
        records = LCSHMixin().get_lcshlinks('Human Rights', 'subject')
        self.assertIn(
            'http://id.loc.gov/authorities/subjects/sh85026379',
            [record['lcsh_id'] for record in records],
            records,
        )
