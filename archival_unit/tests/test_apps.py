from django.apps import apps
from django.test import TestCase
from archival_unit.apps import ArchivalUnitConfig


class ArchivalUnitConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(ArchivalUnitConfig.name, 'archival_unit')
        self.assertEqual(apps.get_app_config('archival_unit').name, 'archival_unit')
