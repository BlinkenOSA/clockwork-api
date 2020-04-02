from django.apps import apps
from django.test import TestCase
from isad.apps import IsadConfig


class IsadConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(IsadConfig.name, 'isad')
        self.assertEqual(apps.get_app_config('isad').name, 'isad')
