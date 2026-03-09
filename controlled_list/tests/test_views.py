from rest_framework import status
from rest_framework.reverse import reverse

from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from controlled_list.tests.helpers import make_access_rights, make_carrier_types


class ControlledListViewTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        make_access_rights(statement="Open")
        make_access_rights(statement="Restricted")
        make_carrier_types(type="Archival Box", width=10)

    def test_access_rights_search(self):
        response = self.client.get(
            reverse("controlled_list-v1:access_rights-select-list"),
            {"search": "Open"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["statement"], "Open")

    def test_carrier_type_select_list(self):
        response = self.client.get(
            reverse("controlled_list-v1:carrier_type-select-list")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["type"], "Archival Box")
