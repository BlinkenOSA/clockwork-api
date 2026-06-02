import json
import logging

from django.conf import settings

from clockwork_api.http import post


logger = logging.getLogger(__name__)


def _get_default_endpoint():
    """
    Returns the Arklet mint endpoint.
    """
    return getattr(settings, "ARK_SERVICE_URL", "https://ark.archivum.org/mint")


def _get_headers():
    """
    Builds Arklet auth headers.
    """
    token = getattr(settings, "ARK_API_TOKEN", None)
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _parse_ark(data):
    """
    Extracts the minted ARK from the Arklet response payload.
    """
    if not isinstance(data, dict):
        return None
    return data.get("ark") or data.get("identifier")


def create_ark_for_record(record_type, record_id, catalog_id=None, reference_code=None):
    """
    Mints a new ARK through Arklet and returns the identifier string.
    """
    ark_service_url = _get_default_endpoint()
    headers = _get_headers()

    naan = getattr(settings, "ARK_NAAN", None)
    shoulder = getattr(settings, "ARK_SHOULDER", None)
    if naan is None or not shoulder:
        logger.error("ARK_NAAN and ARK_SHOULDER must be configured for Arklet minting")
        return None

    target_base = getattr(settings, "CATALOG_URL", None)
    url = f"{target_base.rstrip('/')}/{catalog_id}" if target_base and catalog_id else ""
    metadata = json.dumps({
        "record_type": record_type,
        "record_id": record_id,
        "catalog_id": catalog_id,
        "reference_code": reference_code,
    })
    commitment = getattr(settings, "ARK_COMMITMENT", "")

    payload = {
        "naan": int(naan),
        "shoulder": shoulder,
        "url": url,
        "metadata": metadata,
        "commitment": commitment,
    }

    try:
        response = post(ark_service_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json() if response.content else {}
    except Exception:
        logger.exception("Failed to create ARK via Arklet for %s id=%s", record_type, record_id)
        return None

    return _parse_ark(data)


def ensure_ark(instance, save=True):
    """
    Ensures a published record has an ARK.

    Returns the ARK string when present or successfully minted, otherwise None.
    """
    if getattr(instance, "ark", None):
        return instance.ark
    if not getattr(instance, "published", False):
        return None

    if instance.__class__.__name__ == "FindingAidsEntity":
        record_type = "finding_aids"
        reference_code = instance.archival_reference_code
    elif instance.__class__.__name__ == "Isad":
        record_type = "isad"
        reference_code = instance.reference_code
    else:
        raise ValueError(f"Unsupported ARK model: {instance.__class__.__name__}")

    ark = create_ark_for_record(
        record_type=record_type,
        record_id=instance.id,
        catalog_id=instance.catalog_id,
        reference_code=reference_code,
    )
    if ark and save:
        instance.ark = ark
        instance.save(update_fields=["ark"])
    return ark
