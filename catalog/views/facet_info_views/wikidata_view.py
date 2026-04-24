"""
Wikidata facet enrichment view for the public catalog.

This endpoint now prefers locally cached Wikidata snapshots stored on
authority records and only falls back to a live Wikidata lookup when no
local cache is available yet.
"""

from authority.models import Country, Language, Place, Person, Corporation, Genre, Subject
from authority.services.wikidata_cache import get_best_description, get_wikidata_entity_payload
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

AUTHORITY_MODELS = (
    Country,
    Language,
    Place,
    Person,
    Corporation,
    Genre,
    Subject,
)


class WikidataView(APIView):
    """
    Returns curated Wikidata information for a given Wikidata entity.

    For catalog facet usage we first reuse the payload cached on local
    authority records. This dramatically reduces repeat requests against
    Wikidata and Wikimedia Commons for the same entities.
    """

    permission_classes = []

    def get(self, request, wikidata_id: str, *args, **kwargs) -> Response:
        payload = self._get_local_cached_payload(wikidata_id)
        if payload:
            return Response(payload)

        payload = get_wikidata_entity_payload(wikidata_id)
        if payload:
            self._store_payload_on_authority_record(wikidata_id, payload)
            return Response(payload)

        return Response(status=HTTP_404_NOT_FOUND)

    def _get_local_cached_payload(self, wikidata_id: str):
        for model in AUTHORITY_MODELS:
            record = model.objects.filter(wikidata_id=wikidata_id).only('wikidata_cache').first()
            if record and record.wikidata_cache:
                return record.wikidata_cache
        return None

    def _store_payload_on_authority_record(self, wikidata_id: str, payload):
        for model in AUTHORITY_MODELS:
            record = model.objects.filter(wikidata_id=wikidata_id).first()
            if record:
                model.objects.filter(pk=record.pk).update(
                    wikidata_cache=payload,
                    wikidata_cache_updated_at=timezone.now(),
                )
                return

    def _get_description(self, description):
        return get_best_description(description)
