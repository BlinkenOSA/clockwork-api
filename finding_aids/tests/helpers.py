from finding_aids.models import FindingAidsEntity


def make_finding_aids(container, primary_type, access_rights, **kwargs):
    defaults = {
        'archival_unit': container.archival_unit,
        'container': container,
        'folder_no': 1,
        'description_level': 'L1',
        'access_rights': access_rights,
        'level': 'F',
        'primary_type': primary_type,
        'title': 'Test folder',
        'date_from': '2020-01-01',
        'digital_version_exists': False,
        'digital_version_online': False,
    }
    defaults.update(kwargs)
    return FindingAidsEntity.objects.create(**defaults)