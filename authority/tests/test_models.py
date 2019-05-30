from django.test import TestCase
from authority.models import Country, Language, Place, Person, PersonOtherFormat, Corporation, Genre, Subject


class CountryTest(TestCase):
    """ Test module for Country model """

    def setUp(self):
        Country.objects.create(
            alpha2='AF',
            alpha3='AFG',
            country='Afghanistan'
        )

    def test_str(self):
        country = Country.objects.get(alpha3='AFG')
        self.assertEqual(str(country), country.country)


class LanguageTest(TestCase):
    """ Test module for Language model """

    def setUp(self):
        Language.objects.create(
            iso_639_1='sq',
            iso_639_2='alb',
            language='Albanian'
        )

    def test_str(self):
        language = Language.objects.get(iso_639_2='alb')
        self.assertEqual(str(language), language.language)


class PlaceTest(TestCase):
    """ Test module for Place model """

    def setUp(self):
        Place.objects.create(
            wiki_url='https://en.wikipedia.org/wiki/Budapest',
            place='Budapest'
        )

    def test_str(self):
        place = Place.objects.get(wiki_url='https://en.wikipedia.org/wiki/Budapest')
        self.assertEqual(str(place), place.place)


class PersonTest(TestCase):
    """ Test module for Person model """

    def setUp(self):
        Person.objects.create(
            first_name='Mikhail',
            last_name='Gorbachev',
            wiki_url='https://en.wikipedia.org/wiki/Mikhail_Gorbachev'
        )

    def test_str(self):
        person = Person.objects.get(wiki_url='https://en.wikipedia.org/wiki/Mikhail_Gorbachev')
        self.assertEqual(str(person), "Gorbachev, Mikhail")


class CorporationTest(TestCase):
    """ Test module for Corporation model """

    def setUp(self):
        Corporation.objects.create(
            name='Blinken OSA Archivum',
            wiki_url='https://en.wikipedia.org/wiki/Open_Society_Archives'
        )

    def test_str(self):
        corporation = Corporation.objects.get(wiki_url='https://en.wikipedia.org/wiki/Open_Society_Archives')
        self.assertEqual(str(corporation), corporation.name)


class GenreTest(TestCase):
    """ Test module for Genre model """

    def setUp(self):
        Genre.objects.create(
            genre='Documentary film',
            wiki_url='https://en.wikipedia.org/wiki/Documentary_film'
        )

    def test_str(self):
        genre = Genre.objects.get(wiki_url='https://en.wikipedia.org/wiki/Documentary_film')
        self.assertEqual(str(genre), genre.genre)


class SubjectTest(TestCase):
    """ Test module for Subject model """

    def setUp(self):
        Subject.objects.create(
            subject='Human Rights',
            wiki_url='https://en.wikipedia.org/wiki/Human_rights'
        )

    def test_str(self):
        subject = Subject.objects.get(wiki_url='https://en.wikipedia.org/wiki/Human_rights')
        self.assertEqual(str(subject), subject.subject)
