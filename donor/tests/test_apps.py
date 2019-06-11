from django.apps import apps
from django.test import TestCase
from donor.apps import DonorConfig


class DonorConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(DonorConfig.name, 'donor')
        self.assertEqual(apps.get_app_config('donor').name, 'donor')
