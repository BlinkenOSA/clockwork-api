from django.apps import apps
from django.test import TestCase
from controlled_list.apps import ControlledListConfig


class ControlledListConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(ControlledListConfig.name, 'controlled_list')
        self.assertEqual(apps.get_app_config('controlled_list').name, 'controlled_list')
