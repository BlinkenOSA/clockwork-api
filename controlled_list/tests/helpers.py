from controlled_list.models import AccessRight, ArchivalUnitTheme, CarrierType, PrimaryType


def make_archival_unit_themes(**kwargs):
    defaults = {
        "theme": "Human Rights",
    }
    defaults.update(kwargs)
    return ArchivalUnitTheme.objects.create(**defaults)


def make_access_rights(**kwargs):
    defaults = {
        "statement": "Not Restricted",
    }
    defaults.update(kwargs)
    return AccessRight.objects.create(**defaults)


def make_carrier_types(**kwargs):
    defaults = {
        "type": "Archival boxes",
        "type_original_language": "levéltári doboz",
        "width": 125,
        "height": 265,
        "depth": 320,
    }
    defaults.update(kwargs)
    return CarrierType.objects.create(**defaults)


def make_primary_types(**kwargs):
    defaults = {
        "type": "Moving Image",
    }
    defaults.update(kwargs)
    return PrimaryType.objects.create(**defaults)

