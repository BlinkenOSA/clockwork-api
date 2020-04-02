from django.apps import apps
from django.test import TestCase
from authority.apps import AuthorityConfig


class AuthorityConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(AuthorityConfig.name, 'authority')
        self.assertEqual(apps.get_app_config('authority').name, 'authority')
