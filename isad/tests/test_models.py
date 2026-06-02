from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import patch
from archival_unit.models import ArchivalUnit
from clockwork_api.tests.no_index_signals_mixin import NoIndexSignalsMixin
from isad.models import Isad


class IsadTest(NoIndexSignalsMixin, TestCase):
    """ Test module for Isad model """
    fixtures = ['country']

    def setUp(self):
        self.fonds = ArchivalUnit.objects.create(
            fonds=206,
            level='F',
            title='Records of the Open Society Archives at Central European University'
        )
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()

    def test_save(self):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            year_from=1991
        )
        self.assertEqual(isad.title, self.fonds.title)
        self.assertEqual(isad.reference_code, self.fonds.reference_code)

    @patch("isad.models.ensure_ark")
    def test_publish(self, mock_ensure_ark):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            description_level='F',
            year_from=1991
        )
        isad.publish(self.user)
        self.assertEqual(isad.published, True)
        self.assertEqual(isad.user_published, self.user.username)
        mock_ensure_ark.assert_called_once_with(isad)

    def test_unpublish(self):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            description_level='F',
            year_from=1991
        )
        isad.unpublish()
        self.assertEqual(isad.published, False)
        self.assertEqual(isad.user_published, "")

    @patch("isad.models.ensure_ark")
    def test_publish_creates_ark_when_missing(self, mock_ensure_ark):
        mock_ensure_ark.return_value = "ark:/12345/isad-1"
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            description_level='F',
            year_from=1991
        )

        isad.publish(self.user)

        mock_ensure_ark.assert_called_once_with(isad)

    @patch("isad.models.ensure_ark")
    def test_publish_does_not_create_ark_when_present(self, mock_ensure_ark):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            year_from=1991,
            description_level='F',
            ark="ark:/12345/existing-isad"
        )

        isad.publish(self.user)

        mock_ensure_ark.assert_called_once_with(isad)
