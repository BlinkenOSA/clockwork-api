import json

import meilisearch
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class DashboardSearchView(APIView):
    """
    Unified dashboard search endpoint backed by Meilisearch.

    Supported query params:
        - q: search string
        - limit: number of hits (default: 20, max: 100)
        - offset: pagination offset (default: 0)
        - record_type: optional CSV filter (isad, archival_unit, finding_aids_entity)
    """

    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100

    RECORD_TYPE_ALIASES = {
        'isad': 'isad',
        'archival_unit': 'archival_unit',
        'archivalunit': 'archival_unit',
        'finding_aids': 'finding_aids_entity',
        'finding_aids_entity': 'finding_aids_entity',
        'findingaidsentity': 'finding_aids_entity',
    }

    def get(self, request):
        query = (request.query_params.get('q') or '').strip()
        limit = self._get_int_query_param(request, 'limit', self.DEFAULT_LIMIT)
        offset = self._get_int_query_param(request, 'offset', 0)
        record_types = self._get_record_types(request)
        allowed_archival_unit_ids = self._get_allowed_archival_unit_ids(request)

        if query == '':
            return Response({
                'query': query,
                'count': 0,
                'limit': limit,
                'offset': offset,
                'results': []
            })

        search_payload = {
            'limit': limit,
            'offset': offset
        }

        search_filter = self._build_filter(record_types, allowed_archival_unit_ids)
        if search_filter:
            search_payload['filter'] = search_filter

        try:
            index = self._get_index()
            search_result = index.search(query, search_payload)
        except Exception as exc:
            return Response({
                'detail': 'Search service unavailable.',
                'error': str(exc)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        hits = search_result.get('hits', [])
        results = [self._normalize_hit(hit) for hit in hits]

        return Response({
            'query': query,
            'count': search_result.get('estimatedTotalHits', len(results)),
            'limit': limit,
            'offset': offset,
            'results': results
        })

    def _get_index(self):
        meilisearch_url = getattr(settings, 'MEILISEARCH_URL', '')
        meilisearch_api_key = getattr(settings, 'MEILISEARCH_API_KEY', '')
        index_name = getattr(
            settings,
            'MEILISEARCH_DASHBOARD_SEARCH_INDEX',
            getattr(settings, 'MEILISEARCH_INDEX', 'catalog')
        )

        client = meilisearch.Client(meilisearch_url, meilisearch_api_key)
        return client.index(index_name)

    def _get_int_query_param(self, request, key, default):
        value = request.query_params.get(key, default)
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = default

        if key == 'limit':
            if value <= 0:
                return self.DEFAULT_LIMIT
            return min(value, self.MAX_LIMIT)

        return max(value, 0)

    def _get_record_types(self, request):
        raw_record_type = request.query_params.get('record_type', '')
        if not raw_record_type:
            return []

        record_types = []
        for value in raw_record_type.split(','):
            normalized = self.RECORD_TYPE_ALIASES.get(value.strip().lower())
            if normalized and normalized not in record_types:
                record_types.append(normalized)

        return record_types

    def _get_allowed_archival_unit_ids(self, request):
        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile:
            return []

        return list(user_profile.allowed_archival_units.values_list('id', flat=True))

    def _build_filter(self, record_types, allowed_archival_unit_ids):
        filters = []

        if record_types:
            # Meilisearch filter syntax expects: record_type IN ["a", "b"]
            filters.append('record_type IN %s' % json.dumps(record_types))

        if allowed_archival_unit_ids:
            allowed_ids = json.dumps(allowed_archival_unit_ids)
            filters.append(
                '('
                'archival_unit_id IN {ids} OR '
                'series_id IN {ids} OR '
                '(record_type = "isad" AND ams_id IN {ids}) OR '
                '(record_type = "archival_unit" AND ams_id IN {ids})'
                ')'.format(ids=allowed_ids)
            )

        if not filters:
            return None

        return ' AND '.join(filters)

    def _normalize_hit(self, hit):
        return {
            'id': hit.get('id'),
            'record_type': hit.get('record_type') or self._infer_record_type(hit),
            'title': hit.get('title'),
            'description': (
                hit.get('description')
                or hit.get('contents_summary')
                or hit.get('scope_and_content')
                or hit.get('scope_and_content_abstract')
                or hit.get('scope_and_content_narrative')
            ),
            'reference_code': hit.get('reference_code') or hit.get('call_number'),
            'archival_unit_id': hit.get('archival_unit_id') or hit.get('series_id') or hit.get('ams_id'),
            'source': hit,
        }

    def _infer_record_type(self, hit):
        if hit.get('guid') or hit.get('folder_number') is not None:
            return 'finding_aids_entity'

        if hit.get('description_level') in {'Fonds', 'Subfonds', 'Series'}:
            return 'isad'

        return None
