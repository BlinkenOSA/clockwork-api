from django.apps import apps
from django.test import TestCase
from container.apps import ContainerConfig


class ContainerConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(ContainerConfig.name, 'container')
        self.assertEqual(apps.get_app_config('container').name, 'container')
