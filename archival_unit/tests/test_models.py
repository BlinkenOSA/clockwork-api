from django.contrib.auth.models import User
from django.test import TestCase
from archival_unit.models import ArchivalUnit


class ArchivalUnitTest(TestCase):
    """ Test module for ArchivalUnit model """

    def setUp(self):
        self.fonds = ArchivalUnit.objects.create(
            fonds=206,
            level='F',
            title='Records of the Open Society Archives at Central European University'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=3,
            level='SF',
            title='Public Events',
            parent=self.fonds
        )
        self.series = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=3,
            series=1,
            level='S',
            title='Audiovisual Recordings of Public Events',
            parent=self.subfonds
        )
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()

    def test_get_fonds(self):
        self.assertEqual(self.fonds.get_fonds().id, self.fonds.id)
        self.assertEqual(self.subfonds.get_fonds().id, self.fonds.id)
        self.assertEqual(self.series.get_fonds().id, self.fonds.id)

    def test_get_subfonds(self):
        self.assertEqual(self.fonds.get_subfonds(), None)
        self.assertEqual(self.subfonds.get_subfonds().id, self.subfonds.id)
        self.assertEqual(self.series.get_subfonds().id, self.series.parent.id)

    def test_set_sort(self):
        self.fonds.set_sort()
        self.assertEqual(self.fonds.sort, '020600000000')
        self.subfonds.set_sort()
        self.assertEqual(self.subfonds.sort, '020600030000')
        self.series.set_sort()
        self.assertEqual(self.series.sort, '020600030001')

    def test_set_reference_code(self):
        self.fonds.set_reference_code()
        self.assertEqual(self.fonds.reference_code, 'HU OSA 206')
        self.assertEqual(self.fonds.reference_code_id, 'hu_osa_206')
        self.subfonds.set_reference_code()
        self.assertEqual(self.subfonds.reference_code, 'HU OSA 206-3')
        self.assertEqual(self.subfonds.reference_code_id, 'hu_osa_206-3')
        self.series.set_reference_code()
        self.assertEqual(self.series.reference_code, 'HU OSA 206-3-1')
        self.assertEqual(self.series.reference_code_id, 'hu_osa_206-3-1')

    def test_set_title_full(self):
        self.fonds.set_title_full()
        self.assertEqual(self.fonds.title_full,
                         'HU OSA 206 '
                         'Records of the Open Society Archives at Central European University')
        self.subfonds.set_title_full()
        self.assertEqual(self.subfonds.title_full,
                         'HU OSA 206-3 '
                         'Records of the Open Society Archives at Central European University: '
                         'Public Events')
        self.series.set_title_full()
        self.assertEqual(self.series.title_full,
                         'HU OSA 206-3-1 '
                         'Records of the Open Society Archives at Central European University: '
                         'Public Events: '
                         'Audiovisual Recordings of Public Events')

    def test_set_title_full_zero_subfond(self):
        subfonds = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=0,
            level='SF',
            parent=self.fonds
        )
        series = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=0,
            series=1,
            level='S',
            title='Series with 0 subfonds',
            parent=subfonds
        )
        subfonds.set_title_full()
        self.assertEqual(subfonds.title_full,
                         'HU OSA 206-0 '
                         'Records of the Open Society Archives at Central European University')
        series.set_title_full()
        self.assertEqual(series.title_full,
                         'HU OSA 206-0-1 '
                         'Records of the Open Society Archives at Central European University: '
                         'Series with 0 subfonds')