# clockwork_api
API for the Clockwork Archival Management System @ Blinken OSA

[![Build Status](https://www.travis-ci.org/BlinkenOSA/clockwork_api.svg?branch=development)](https://www.travis-ci.org/BlinkenOSA/clockwork_api)

## Finding aids Meilisearch indexing

`FindingAidsMeilisearchIndexer` accepts `target="ams"` (the default) or
`target="catalog"`. Configure the destinations in Django settings, for example
in `clockwork_api/settings_components/local.py`:

```python
MEILISEARCH_URL = "http://localhost:7700"
MEILISEARCH_AMS_API_KEY = "<ams indexing key>"
MEILISEARCH_AMS_INDEX = "ams"
MEILISEARCH_CATALOG_API_KEY = "<catalog indexing key>"
MEILISEARCH_CATALOG_INDEX = "catalog"
```

Finding aids and ISAD indexing for AMS, along with dashboard search, use
`MEILISEARCH_AMS_API_KEY` and `MEILISEARCH_AMS_INDEX`. Dashboard search also
retains its legacy `MEILISEARCH_DASHBOARD_SEARCH_INDEX` fallback. Catalog
indexing requires both catalog settings.

```python
FindingAidsMeilisearchIndexer(finding_aids_entity_id, target="catalog").index()
```

The index and removal Celery tasks also accept `target`. Automatic updates from
finding aids signals use the default AMS target. To run a catalog test reindex:

```shell
python manage.py index_finding_aids_entities_meilisearch --target catalog --fonds 300 --subfonds 1 --series 1
```

Use `--target ams` for dashboard indexing.

LCSH endpoint tests mock Library of Congress responses so normal test runs do not
depend on that service. To run the separate live checks explicitly:

```sh
RUN_LCSH_LIVE_TESTS=1 python manage.py test authority.tests.test_lcsh_live
```

These checks require network access and may fail if LoC is unavailable or blocks
the runner. Upstream HTTP failures and request errors are logged by
`authority.views.lcsh_views` at warning level.
