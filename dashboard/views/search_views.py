import json
import re

import meilisearch
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class DashboardSearchView(APIView):
    """
    Unified dashboard search endpoint backed by Meilisearch.

    Supported query params:
        - q / search: search string
        - limit: number of hits (default: 20, max: 100)
        - offset: pagination offset (default: 0)
        - record_type: optional CSV filter (isad, archival_unit, finding_aids_entity)
        - highlight: optional boolean flag to return highlighted snippets
        - highlight_fields: optional CSV of fields to highlight (default: all)
        - facets are returned for: series_reference_code, record_type, primary_type
    """

    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100
    FACET_FIELDS = ['series_reference_code', 'record_type', 'description_level']
    RESERVED_QUERY_PARAMS = {
        'q',
        'search',
        'limit',
        'offset',
        'record_type',
        'highlight',
        'highlight_fields',
    }
    FACET_FIELD_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

    RECORD_TYPE_ALIASES = {
        'isad': 'isad',
        'archival_unit': 'archival_unit',
        'archivalunit': 'archival_unit',
        'finding_aids': 'finding_aids_entity',
        'finding_aids_entity': 'finding_aids_entity',
        'findingaidsentity': 'finding_aids_entity',
    }

    def get(self, request):
        query = (request.query_params.get('search') or request.query_params.get('q') or '').strip()
        limit = self._get_int_query_param(request, 'limit', self.DEFAULT_LIMIT)
        offset = self._get_int_query_param(request, 'offset', 0)
        record_types = self._get_record_types(request)
        allowed_archival_unit_ids = self._get_allowed_archival_unit_ids(request)
        dynamic_facet_filters = self._get_dynamic_facet_filters(request)
        highlight = self._get_bool_query_param(request, 'highlight', True)
        highlight_fields = self._get_highlight_fields(request)

        if query == '':
            return Response({
                'query': query,
                'count': 0,
                'limit': limit,
                'offset': offset,
                'facets': {},
                'results': []
            })

        search_payload = {
            'limit': limit,
            'offset': offset,
            'facets': self.FACET_FIELDS,
            'attributesToCrop': ['contents_summary', 'contents_summary_original'],
            "cropLength": 20
        }

        if highlight:
            search_payload['attributesToHighlight'] = highlight_fields or ['*']
            search_payload['highlightPreTag'] = '<mark>'
            search_payload['highlightPostTag'] = '</mark>'

        search_filter = self._build_filter(record_types, allowed_archival_unit_ids, dynamic_facet_filters)
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
        if highlight:
            results = [self._with_highlights(hit) for hit in hits]
        else:
            results = hits

        return Response({
            'query': query,
            'count': search_result.get('estimatedTotalHits', len(results)),
            'limit': limit,
            'offset': offset,
            'highlight': highlight,
            'facets': search_result.get('facetDistribution', {}),
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

    def _get_bool_query_param(self, request, key, default=False):
        value = request.query_params.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def _get_highlight_fields(self, request):
        raw_value = request.query_params.get('highlight_fields', '')
        if not raw_value:
            return []

        fields = []
        for value in raw_value.split(','):
            normalized = value.strip()
            if normalized and normalized not in fields:
                fields.append(normalized)
        return fields

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

    def _build_filter(self, record_types, allowed_archival_unit_ids, dynamic_facet_filters):
        filters = []

        if record_types:
            # Meilisearch filter syntax expects: record_type IN ["a", "b"]
            filters.append('record_type IN %s' % json.dumps(record_types))

        if allowed_archival_unit_ids:
            allowed_ids = json.dumps(allowed_archival_unit_ids)
            filters.append('archival_unit_id IN {ids}'.format(ids=allowed_ids))

        for field_name, values in dynamic_facet_filters.items():
            if len(values) == 1:
                filters.append('{field} = {value}'.format(
                    field=field_name,
                    value=json.dumps(values[0])
                ))
            elif len(values) > 1:
                filters.append('{field} IN {values}'.format(
                    field=field_name,
                    values=json.dumps(values)
                ))

        if not filters:
            return None

        return ' AND '.join(filters)

    def _get_dynamic_facet_filters(self, request):
        facet_filters = {}

        for key, values in request.query_params.lists():
            if key in self.RESERVED_QUERY_PARAMS:
                continue

            if not self.FACET_FIELD_PATTERN.match(key):
                continue

            normalized_values = []
            for raw_value in values:
                for value_part in str(raw_value).split(','):
                    normalized = value_part.strip()
                    if normalized and normalized not in normalized_values:
                        normalized_values.append(normalized)

            if normalized_values:
                facet_filters[key] = normalized_values

        return facet_filters

    def _infer_record_type(self, hit):
        if hit.get('guid') or hit.get('folder_number') is not None:
            return 'finding_aids_entity'

        if hit.get('description_level') in {'Fonds', 'Subfonds', 'Series'}:
            return 'isad'

        return None

    def _with_highlights(self, hit):
        result = dict(hit)
        result['highlights'] = hit.get('_formatted', {})
        return result
