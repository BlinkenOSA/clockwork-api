from controlled_list.models import ArchivalUnitTheme


def make_archival_unit_themes(**kwargs):
    defaults = {
        "theme": "Human Rights",
    }
    defaults.update(kwargs)
    return ArchivalUnitTheme.objects.create(**defaults)