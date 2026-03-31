from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.reverse import reverse

from audit_log.models import AuditLog
from audit_log.serializers import AuditLogReadSerializer
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class AuditLogModelTests(TestCase):
    def test_str_representation(self):
        user = User.objects.create_user(username='alice', password='secret')
        log = AuditLog.objects.create(
            user=user,
            action='UPDATE',
            model_name='archival_unit.ArchivalUnit',
            object_id=42
        )
        self.assertEqual(str(log), 'alice UPDATE archival_unit.ArchivalUnit (ID: 42)')


class AuditLogSerializerTests(TestCase):
    def test_user_serialized_as_username(self):
        user = User.objects.create_user(username='bob', password='secret')
        log = AuditLog.objects.create(
            user=user,
            action='CREATE',
            model_name='accession.Accession',
            object_id=1
        )
        data = AuditLogReadSerializer(log).data
        self.assertEqual(data['user'], 'bob')


class AuditLogViewTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        self.log1 = AuditLog.objects.create(
            user=self.user,
            action='CREATE',
            model_name='archival_unit.ArchivalUnit',
            object_id=1
        )
        self.log2 = AuditLog.objects.create(
            user=self.user,
            action='UPDATE',
            model_name='archival_unit.ArchivalUnit',
            object_id=2
        )
        self.log3 = AuditLog.objects.create(
            user=self.user,
            action='UPDATE',
            model_name='accession.Accession',
            object_id=2
        )

    def test_list_filters_by_action(self):
        response = self.client.get(
            reverse('audit-log-v1:audit-log-list'),
            {'action': 'UPDATE'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_filters_by_model_name_and_object_id(self):
        response = self.client.get(
            reverse('audit-log-v1:audit-log-list'),
            {'model_name': 'archival_unit.ArchivalUnit', 'object_id': 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['object_id'], 2)
