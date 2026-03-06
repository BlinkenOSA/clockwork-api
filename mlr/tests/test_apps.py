from django.apps import apps
from django.test import TestCase

from mlr.apps import MLRConfig


class MLRConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(MLRConfig.name, 'mlr')
        self.assertEqual(apps.get_app_config('mlr').name, 'mlr')
