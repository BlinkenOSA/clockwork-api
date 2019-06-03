from django.test import TestCase
from authority.models import Country, Language, Place, Person, PersonOtherFormat, Corporation, Genre, Subject


class PersonTest(TestCase):
    """ Test module for Person model """

    def setUp(self):
        Person.objects.create(
            first_name='Mikhail',
            last_name='Gorbachev',
            wiki_url='https://en.wikipedia.org/wiki/Mikhail_Gorbachev'
        )

    def test_name(self):
        person = Person.objects.get(wiki_url='https://en.wikipedia.org/wiki/Mikhail_Gorbachev')
        self.assertEqual(person.name, "Gorbachev, Mikhail")