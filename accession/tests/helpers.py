from accession.models import Accession, AccessionMethod
from archival_unit.tests.helpers import make_fonds
from donor.tests.helpers import make_donor


def make_accession(**kwargs):
    fonds = make_fonds()
    method = make_accession_method()
    donor = make_donor()
    defaults = {
        'title': 'Test accession',
        'transfer_date': '1995-05-01',
        'archival_unit': fonds,
        'method': method,
        'donor': donor
    }
    defaults.update(kwargs)
    return Accession.objects.create(**defaults)

def make_accession_items(**kwargs):
    accession = make_accession()
    defaults = {
        'accession': accession,
        'description': 'Test item',
        'quantity': 1,
    }
    defaults.update(kwargs)
    return accession.accessionitem_set.create(**defaults)

def make_accession_method(**kwargs):
    defaults = {
        'method': 'Deposit (CEU)',
    }
    defaults.update(kwargs)
    return AccessionMethod.objects.create(**defaults)