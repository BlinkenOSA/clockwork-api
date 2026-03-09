from authority.models import Country


def make_country(**kwargs):
    defaults = {
        "alpha2": "HU",
        "alpha3": "HUN",
        "country": "Hungary",
    }
    defaults.update(kwargs)
    return Country.objects.create(**defaults)