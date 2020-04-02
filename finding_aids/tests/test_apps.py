from django.apps import apps
from django.test import TestCase
from finding_aids.apps import FindingAidsConfig


class FindingAidsConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(FindingAidsConfig.name, 'finding_aids')
        self.assertEqual(apps.get_app_config('finding_aids').name, 'finding_aids')
