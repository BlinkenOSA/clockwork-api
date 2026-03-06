from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from controlled_list.models import ArchivalUnitTheme


class ArchivalUnitViewTest(TestViewsBaseClass):
    """ Testing ArchivalUnit endpoint """
    fixtures = ['archival_unit_themes']

    def setUp(self):
        self.init()
        self.fonds = ArchivalUnit.objects.create(
            fonds=206,
            level='F',
            title='Records of the Open Society Archives at Central European University'
        )
        self.fonds.theme.add(ArchivalUnitTheme.objects.get(theme='Human Rights'))

    def test_mixin_for_read_serializer(self):
        response = self.client.get(reverse('archival_unit-v1:archival_unit-detail', kwargs={'pk': self.fonds.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['theme'][0], 2)

    def test_mixin_for_view_serializer(self):
        subfonds = {
            'fonds': 206,
            'subfonds': 3,
            'level': 'SF',
            'title': 'Public Events',
            'parent': self.fonds.id
        }
        response = self.client.post(reverse('archival_unit-v1:archival_unit-list'), data=subfonds)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], self.fonds.id)

    def test_mixin_for_not_allowed_method(self):
        response = self.client.put(reverse('archival_unit-v1:archival_unit-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_for_user_created(self):
        subfonds = {
            'fonds': 206,
            'subfonds': 3,
            'level': 'SF',
            'title': 'Public Events',
            'parent': self.fonds.id
        }
        response = self.client.post(reverse('archival_unit-v1:archival_unit-list'), data=subfonds)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_created'], self.user.username)

    def test_update_for_user_updated(self):
        response = self.client.patch(reverse('archival_unit-v1:archival_unit-detail',
                                             kwargs={'pk': self.fonds.pk}),
                                     data={'title': 'Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
        self.assertEqual(response.data['user_updated'], self.user.username)

    def test_precreate_endpoint_for_fonds(self):
        response = self.client.get(reverse('archival_unit-v1:archival_unit-pre-create',
                                           kwargs={'pk': self.fonds.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['parent'], self.fonds.id)
        self.assertEqual(response.data['level'], 'SF')

    def test_select_by_parent_respects_allowed_units(self):
        subfonds_allowed = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=1,
            level='SF',
            title='Allowed Subfonds',
            parent=self.fonds
        )
        subfonds_blocked = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=2,
            level='SF',
            title='Blocked Subfonds',
            parent=self.fonds
        )
        series_allowed = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=1,
            series=1,
            level='S',
            title='Allowed Series',
            parent=subfonds_allowed
        )
        ArchivalUnit.objects.create(
            fonds=206,
            subfonds=2,
            series=1,
            level='S',
            title='Blocked Series',
            parent=subfonds_blocked
        )
        self.user_profile.allowed_archival_units.add(series_allowed)

        response = self.client.get(
            reverse('archival_unit-v1:archival_unit-select-by-parent-list', kwargs={'parent_id': self.fonds.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data}
        self.assertEqual(returned_ids, {subfonds_allowed.id})

        response = self.client.get(
            reverse('archival_unit-v1:archival_unit-select-by-parent-list', kwargs={'parent_id': subfonds_allowed.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data}
        self.assertEqual(returned_ids, {series_allowed.id})
