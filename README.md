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

## Semantic Solr indexing

Configure the semantic destination separately from the existing catalog in
`clockwork_api/settings_components/local.py`:

```python
import os

SEMANTIC_SOLR_URL = "https://solr10.archivum.org/solr/catalog"
SEMANTIC_SOLR_USERNAME = os.environ.get("SEMANTIC_SOLR_USERNAME", "")
SEMANTIC_SOLR_PASSWORD = os.environ.get("SEMANTIC_SOLR_PASSWORD", "")
```

Both semantic indexers and `index_semantic_catalog_slice` use these settings.
If a semantic credential setting is absent, its corresponding `SOLR_USERNAME`
or `SOLR_PASSWORD` setting is used. If `SEMANTIC_SOLR_URL` is absent, direct
indexers build the URL from `SOLR_URL` and `SOLR_CORE_CATALOG_NEW`; the command
retains its default of `http://localhost:8983/solr/catalog`. Set both semantic
credentials to empty strings for an unauthenticated local instance; a partial
credential pair is rejected.

Choose the indexing scope by supplying a fonds, an optional subfonds and series,
or `--all` for the entire catalog. The command includes ISAD(G) records and
finding aids for every matching archival unit, retaining each series' own
semantic context. Unpublished records and finding aids templates are skipped.

```shell
python manage.py index_semantic_catalog_slice --fonds 300
python manage.py index_semantic_catalog_slice --fonds 300 --subfonds 1
python manage.py index_semantic_catalog_slice --fonds 300 --subfonds 1 --series 1
python manage.py index_semantic_catalog_slice --all
```

`--series` requires `--subfonds`. `--all` cannot be combined with hierarchy
filters. Add `--dry-run` to preview semantic text without writing to Solr or
calling the embedding service.

The command also accepts per-run overrides:

```shell
python manage.py index_semantic_catalog_slice \
  --fonds 300 --subfonds 1 --series 1 \
  --solr-url https://solr10.archivum.org/solr/catalog \
  --solr-username solradmin --solr-password '<password>'
```

Prefer the environment-backed settings above to keep the password out of
shell history and process arguments. With those configured, omit the two
credential flags. The embedding service does not receive Solr credentials.

Solr updates and the final commit use a dedicated 60-second timeout, independent
of the application's `REQUESTS_TIMEOUT`. Timeouts, connection failures, and HTTP
408, 429, 500, 502, 503, or 504 responses are retried up to five times, with
exponential delays starting at one second and capped at 30 seconds. Each retry
is logged to stderr with the document ID (or commit). The same document and
embedding are reused, so retries replace the same Solr ID without generating
another embedding. Other HTTP errors fail immediately; exhausting retries stops
the command with the failed document ID or commit in the error.

Override these defaults with `SEMANTIC_SOLR_TIMEOUT` and
`SEMANTIC_SOLR_MAX_RETRIES` in the environment or Django settings, or per run:

```shell
python manage.py index_semantic_catalog_slice --all \
  --solr-timeout 120 --solr-max-retries 8
```

The timeout must be positive. Set `--solr-max-retries 0` to disable retries.

### Embedding service URL and authentication

Clockwork reads these environment variables for `index_semantic_catalog_slice`.
Set them in the Clockwork process environment, for example in your deployment's
environment file:

```text
SEMANTIC_EMBEDDING_BASE_URL=https://embedder.example.org
SEMANTIC_EMBEDDING_USERNAME=tester
SEMANTIC_EMBEDDING_PASSWORD=your-password
```

These defaults are defined in `settings_components/production.py` and can also
be overridden with the same names in Django's `settings_components/local.py`.
The URL is the service base URL, without `/embed`. A proxy subpath is supported:
`https://example.org/embedder/` sends requests to
`https://example.org/embedder/embed`. Without configuration, the existing
`http://localhost:8000` base URL remains the default.

Both credentials are optional; leave both empty for an unauthenticated
embedder. These credentials authenticate to the Apache-protected embedder
and are separate from `SEMANTIC_SOLR_USERNAME` / `SEMANTIC_SOLR_PASSWORD`.
A partial credential pair is rejected before records are loaded or indexed.

The command accepts per-run overrides:

```shell
python manage.py index_semantic_catalog_slice \
  --fonds 300 --subfonds 1 --series 1 \
  --embedding-base-url https://example.org/embedder \
  --embedding-username tester --embedding-password '<password>'
```

Prefer the environment-backed settings to keep the password out of process
arguments and shell history. To override configured authentication for a local
run, pass both `--embedding-username '' --embedding-password ''`. Existing
`--embedding-timeout` / `SEMANTIC_EMBEDDING_TIMEOUT` settings still apply.

### Direct Solr indexer overrides

Direct indexer use supports the same overrides:

```python
FindingAidsSemanticIndexer(
    finding_aids_entity_id,
    solr_url="https://solr10.archivum.org/solr/catalog",
    solr_username="solradmin",
    solr_password=password,
).index()
```

`ISADSemanticIndexer` accepts the same keyword arguments. The selected
credentials apply to indexing, commits, and deletes.

LCSH endpoint tests mock Library of Congress responses so normal test runs do not
depend on that service. To run the separate live checks explicitly:

```sh
RUN_LCSH_LIVE_TESTS=1 python manage.py test authority.tests.test_lcsh_live
```

These checks require network access and may fail if LoC is unavailable or blocks
the runner. Upstream HTTP failures and request errors are logged by
`authority.views.lcsh_views` at warning level.
