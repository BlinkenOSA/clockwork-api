from archival_unit.models import ArchivalUnit
from controlled_list.models import Locale


def make_fonds(**kwargs):
    defaults = {
        "uuid": "fe993201-9fab-4f8c-9961-c6ed26e70e8b",
        "fonds": 206,
        "subfonds": 0,
        "series": 0,
        "sort": "020600000000",
        "title": "Records of the Open Society Archives at Central European University",
        "title_full": "HU OSA 206 Records of the Open Society Archives at Central European University",
        "acronym": "OSA Archivum",
        "reference_code": "HU OSA 206",
        "reference_code_id": "hu_osa_206",
        "level": "F",
        "status": "Final",
        "ready_to_publish": False,
        "user_created": "finding.aids",
        "date_created": "2018-05-07T08:24:22",
        "user_updated": "finding.aids",
        "date_updated": "2018-05-07T08:24:22",
    }
    defaults.update(kwargs)
    return ArchivalUnit.objects.create(**defaults)

def make_subfonds(fonds, **kwargs):
    locale = Locale.objects.create(pk='HU', locale_name='Hungarian')
    defaults = {
        "uuid": "87a764d5-1583-4563-b68b-91df00ad9af6",
        "parent": fonds,
        "fonds": 206,
        "subfonds": 3,
        "series": 0,
        "sort": "020600030000",
        "title": "Public Events",
        "title_full": "HU OSA 206-3 Records of the Open Society Archives at Central European University: Public Events",
        "title_original": "Konferenciák és egyéb rendezvények",
        "original_locale": locale,
        "reference_code": "HU OSA 206-3",
        "reference_code_id": "hu_osa_206-3",
        "level": "SF",
        "status": "Final",
        "ready_to_publish": False,
        "user_created": "finding.aids",
        "date_created": "2018-05-07T08:24:25",
        "user_updated": "finding.aids",
        "date_updated": "2020-04-28T15:12:57",
      }
    defaults.update(kwargs)
    return ArchivalUnit.objects.create(**defaults)

def make_series(subfonds, **kwargs):
    defaults = {
        "uuid": "98d10b78-aa2b-40e7-b647-b087f61c28b9",
        "parent": subfonds,
        "fonds": 206,
        "subfonds": 3,
        "series": 1,
        "sort": "020600030001",
        "title": "Audiovisual Recordings of Public Events",
        "title_full": "HU OSA 206-3-1 Records of the Open Society Archives at Central European University: Public Events: Audiovisual Recordings of Public Events",
        "reference_code": "HU OSA 206-3-1",
        "reference_code_id": "hu_osa_206-3-1",
        "level": "S",
        "status": "Final",
        "ready_to_publish": False,
        "user_created": "finding.aids",
        "date_created": "2018-05-07T08:24:31",
        "user_updated": "",
        "date_updated": "2018-05-07T08:24:31"
    }
    defaults.update(kwargs)
    return ArchivalUnit.objects.create(**defaults)