from urllib.parse import unquote, urlparse

from django.conf import settings

from clockwork_api.http import get

WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
VIAF_PROPERTY = "P214"


def _extract_wikipedia_article(url: str):
    if not url:
        return None, None

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if ".wikipedia.org" not in hostname:
        return None, None

    language = hostname.split(".wikipedia.org")[0]
    prefix = "/wiki/"
    if not parsed.path.startswith(prefix):
        return None, None

    title = unquote(parsed.path[len(prefix):]).strip()
    if not language or not title:
        return None, None

    return language, title


def _extract_viaf_id(url: str):
    if not url:
        return None

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if "viaf.org" not in hostname:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] != "viaf":
        return None

    viaf_id = parts[1]
    return viaf_id if viaf_id.isdigit() else None


def resolve_wikidata_id_from_wikipedia_url(url: str):
    language, title = _extract_wikipedia_article(url)
    if not language or not title:
        return None

    response = get(
        f"https://{language}.wikipedia.org/w/api.php",
        headers={"User-Agent": settings.WIKIDATA_USER_AGENT},
        params={
            "action": "query",
            "prop": "pageprops",
            "titles": title,
            "format": "json",
        },
    )
    if response.status_code != 200:
        return None

    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        wikidata_id = page.get("pageprops", {}).get("wikibase_item")
        if wikidata_id:
            return wikidata_id

    return None


def resolve_wikidata_id_from_viaf_url(url: str):
    viaf_id = _extract_viaf_id(url)
    if not viaf_id:
        return None

    query = f'SELECT ?item WHERE {{ ?item wdt:{VIAF_PROPERTY} "{viaf_id}" . }} LIMIT 1'
    response = get(
        WIKIDATA_API_URL,
        params={
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "type": "item",
            "search": f'haswbstatement:{VIAF_PROPERTY}={viaf_id}',
        },
    )
    if response.status_code == 200:
        for result in response.json().get("search", []):
            concept_uri = result.get("concepturi", "")
            if concept_uri.endswith(result.get("id", "")) and result.get("id", "").startswith("Q"):
                return result["id"]

    response = get(
        WIKIDATA_SPARQL_URL,
        headers={"Accept": "application/sparql-results+json"},
        params={
            "format": "json",
            "query": query,
        },
    )
    if response.status_code != 200:
        return None

    bindings = response.json().get("results", {}).get("bindings", [])
    if not bindings:
        return None

    entity_url = bindings[0].get("item", {}).get("value", "")
    if "/entity/Q" not in entity_url:
        return None

    return entity_url.rsplit("/", 1)[-1]


def resolve_authority_wikidata_id(wiki_url: str = "", authority_url: str = ""):
    wikipedia_id = resolve_wikidata_id_from_wikipedia_url(wiki_url)
    viaf_id = resolve_wikidata_id_from_viaf_url(authority_url)

    if wikipedia_id and viaf_id and wikipedia_id != viaf_id:
        return None, {
            "status": "conflict",
            "wikipedia_id": wikipedia_id,
            "viaf_id": viaf_id,
        }

    resolved_id = wikipedia_id or viaf_id
    if wikipedia_id and viaf_id:
        source = "wikipedia+viaf"
    elif wikipedia_id:
        source = "wikipedia"
    elif viaf_id:
        source = "viaf"
    else:
        source = None

    return resolved_id, {
        "status": "resolved" if resolved_id else "missing",
        "source": source,
        "wikipedia_id": wikipedia_id,
        "viaf_id": viaf_id,
    }


def resolve_person_wikidata_id(wiki_url: str = "", authority_url: str = ""):
    return resolve_authority_wikidata_id(wiki_url=wiki_url, authority_url=authority_url)


def resolve_corporation_wikidata_id(wiki_url: str = "", authority_url: str = ""):
    return resolve_authority_wikidata_id(wiki_url=wiki_url, authority_url=authority_url)
