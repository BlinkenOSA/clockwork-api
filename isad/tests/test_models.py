from django.contrib.auth.models import User
from django.test import TestCase
from archival_unit.models import ArchivalUnit
from isad.models import Isad


class IsadTest(TestCase):
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

    def test_publish(self):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            year_from=1991
        )
        isad.publish(self.user)
        self.assertEqual(isad.published, True)
        self.assertEqual(isad.user_published, self.user.username)

    def test_unpublish(self):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            year_from=1991
        )
        isad.unpublish()
        self.assertEqual(isad.published, False)
        self.assertEqual(isad.user_published, "")