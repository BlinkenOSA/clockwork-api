from container.models import Container


def make_container(series, carrier_type, **kwargs):
    defaults = {
        "archival_unit": series,
        "carrier_type": carrier_type,
        "container_no": 1,
    }
    defaults.update(kwargs)
    return Container.objects.create(**defaults)
