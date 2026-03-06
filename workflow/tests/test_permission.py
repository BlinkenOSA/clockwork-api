from django.contrib.auth.models import Group, User
from django.test import TestCase

from workflow.permission import APIGroupPermission


class APIGroupPermissionTests(TestCase):
    def test_has_permission_true_for_api_group_member(self):
        user = User.objects.create_user(username='api_user', password='secret')
        group = Group.objects.create(name='Api')
        user.groups.add(group)

        request = type('Request', (), {'user': user})
        permission = APIGroupPermission()

        self.assertTrue(permission.has_permission(request, None))

    def test_has_permission_false_for_non_member(self):
        user = User.objects.create_user(username='plain_user', password='secret')

        request = type('Request', (), {'user': user})
        permission = APIGroupPermission()

        self.assertFalse(permission.has_permission(request, None))
