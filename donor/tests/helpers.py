from authority.tests.helpers import make_country
from donor.models import Donor


def make_donor(**kwargs):
    country = make_country()
    defaults = {
        'name': 'John, Doe',
        'first_name': 'John',
        'last_name': 'Doe',
        'postal_code': '1051',
        'country': country,
        'city': 'Budapest',
        'address': 'Arany Janos u. 32.',
        'email': 'info@osaarchivum.org'
    }
    defaults.update(kwargs)
    return Donor.objects.create(**defaults)
