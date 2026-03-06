from django.apps import apps
from django.contrib.auth.models import User, Group
from django.test import TestCase
from rest_framework.authtoken.models import Token

from accounts.apps import AccountsConfig
from accounts.models import UserProfile
from accounts.serializers import CurrentUserSerializer
from archival_unit.models import ArchivalUnit


class AccountsConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(AccountsConfig.name, 'accounts')
        self.assertEqual(apps.get_app_config('accounts').name, 'accounts')


class UserProfileTests(TestCase):
    def test_assigned_archival_units_count_and_str(self):
        user = User.objects.create_user(username='alice', password='secret')
        profile = UserProfile.objects.create(user=user)

        au = ArchivalUnit.objects.create(
            fonds=1,
            subfonds=0,
            series=0,
            level='F',
            title='Test Fonds'
        )
        profile.allowed_archival_units.add(au)

        self.assertEqual(profile.assigned_archival_units(), 1)
        self.assertEqual(str(profile), 'alice')


class AuthTokenSignalTests(TestCase):
    def test_creates_token_on_user_create(self):
        user = User.objects.create_user(username='bob', password='secret')
        self.assertTrue(Token.objects.filter(user=user).exists())


class CurrentUserSerializerTests(TestCase):
    def test_serializes_groups_and_admin_flag(self):
        user = User.objects.create_superuser(username='admin', password='secret', email='a@example.com')
        group = Group.objects.create(name='editors')
        user.groups.add(group)

        data = CurrentUserSerializer(user).data

        self.assertTrue(data['is_admin'])
        self.assertIn('editors', data['groups'])
