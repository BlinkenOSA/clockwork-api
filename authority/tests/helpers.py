from authority.models import Country, Genre
from authority.models import Language


def make_country(**kwargs):
    defaults = {
        "alpha2": "HU",
        "alpha3": "HUN",
        "country": "Hungary",
    }
    defaults.update(kwargs)
    return Country.objects.create(**defaults)

def make_language(**kwargs):
    defaults = {
        "iso_639_1": "hu",
        "iso_639_2": "hun",
        "language": "Hungarian",
    }
    defaults.update(kwargs)
    return Language.objects.create(**defaults)

def make_genre(**kwargs):
    defaults = {
        "genre": "Feature Film",
    }
    defaults.update(kwargs)
    return Genre.objects.create(**defaults)