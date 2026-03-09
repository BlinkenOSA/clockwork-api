from accession.models import Accession, AccessionMethod


def make_accession(fonds, method, donor, **kwargs):
    defaults = {
        'title': 'Test accession',
        'transfer_date': '1995-05-01',
        'archival_unit': fonds,
        'method': method,
        'donor': donor
    }
    defaults.update(kwargs)
    return Accession.objects.create(**defaults)

def make_accession_items(accession, **kwargs):
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