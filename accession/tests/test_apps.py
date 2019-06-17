from django.apps import apps
from django.test import TestCase

from accession.apps import AccessionConfig


class AccessionConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(AccessionConfig.name, 'accession')
        self.assertEqual(apps.get_app_config('accession').name, 'accession')
