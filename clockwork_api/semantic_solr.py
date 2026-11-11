from django.conf import settings
from requests.auth import HTTPBasicAuth


def get_semantic_solr_url():
    """Use the semantic core URL, falling back to the existing catalog settings."""
    return getattr(
        settings,
        "SEMANTIC_SOLR_URL",
        "%s/%s" % (
            getattr(settings, "SOLR_URL", "http://localhost:8983/solr").rstrip("/"),
            getattr(settings, "SOLR_CORE_CATALOG_NEW", "catalog"),
        ),
    ).rstrip("/")


def get_semantic_solr_auth(username=None, password=None):
    """Resolve explicit credentials before semantic and legacy Django settings."""
    if username is None:
        username = getattr(settings, "SEMANTIC_SOLR_USERNAME", getattr(settings, "SOLR_USERNAME", None))
    if password is None:
        password = getattr(settings, "SEMANTIC_SOLR_PASSWORD", getattr(settings, "SOLR_PASSWORD", None))

    if bool(username) != bool(password):
        raise ValueError("Solr authentication requires both a username and a password.")
    if username and password:
        return HTTPBasicAuth(username, password)
    return None
