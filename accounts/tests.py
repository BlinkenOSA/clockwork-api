from django.apps import apps
from django.contrib.auth.models import User, Group
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token

from accounts.apps import AccountsConfig
from accounts.admin import UserProfileInlineForm
from accounts.models import UserProfile
from accounts.serializers import CurrentUserSerializer
from archival_unit.models import ArchivalUnit
from archival_unit.tests.helpers import make_fonds


class AccountsConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(AccountsConfig.name, 'accounts')
        self.assertEqual(apps.get_app_config('accounts').name, 'accounts')


class UserProfileTests(TestCase):
    def test_assigned_archival_units_count_and_str(self):
        user = User.objects.create_user(username='alice', password='secret')
        profile = UserProfile.objects.create(user=user)
        au = make_fonds()
        profile.allowed_archival_units.add(au)

        self.assertEqual(profile.assigned_archival_units(), 1)
        self.assertEqual(str(profile), 'alice')

    @override_settings(UNPROCESSED_MATERIALS_FONDS=999)
    def test_admin_limits_unprocessed_choices_to_configured_fonds_series(self):
        unprocessed_fonds = ArchivalUnit.objects.create(
            fonds=999,
            level='F',
            title='Unprocessed materials',
        )
        unprocessed_subfonds = ArchivalUnit.objects.create(
            fonds=999,
            subfonds=1,
            level='SF',
            title='Unprocessed audiovisual materials',
            parent=unprocessed_fonds,
        )
        unprocessed_series = ArchivalUnit.objects.create(
            fonds=999,
            subfonds=1,
            series=1,
            level='S',
            title='Unprocessed series',
            parent=unprocessed_subfonds,
        )
        regular_fonds = ArchivalUnit.objects.create(
            fonds=206,
            level='F',
            title='Regular fonds',
        )
        regular_subfonds = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=1,
            level='SF',
            title='Regular subfonds',
            parent=regular_fonds,
        )
        ArchivalUnit.objects.create(
            fonds=206,
            subfonds=1,
            series=1,
            level='S',
            title='Regular series',
            parent=regular_subfonds,
        )

        form = UserProfileInlineForm()

        self.assertEqual(
            list(form.fields['allowed_unprocessed_series'].queryset),
            [unprocessed_series],
        )


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
