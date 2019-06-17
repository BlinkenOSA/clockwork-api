from django.apps import apps
from django.test import TestCase
from isaar.apps import IsaarConfig


class IsaarConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(IsaarConfig.name, 'isaar')
        self.assertEqual(apps.get_app_config('isaar').name, 'isaar')
