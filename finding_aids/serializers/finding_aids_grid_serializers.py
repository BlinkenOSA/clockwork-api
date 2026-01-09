from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.models import AccessRight
from finding_aids.models import FindingAidsEntity


class FindingAidsGridSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Serializer for grid/table editing of finding aids entities.

    Intended for UI "bulk edit" or spreadsheet-like views where a curated subset
    of fields is displayed and edited inline.

    Notes:
        - Uses a SlugRelatedField for access_rights so the grid can work with
          the human-readable statement values.
        - Includes both localized/original fields where applicable.
        - Uses WritableNestedModelSerializer for consistency with other finding_aids
          serializers, even though this serializer is primarily flat.
    """

    access_rights = serializers.SlugRelatedField(slug_field='statement', queryset=AccessRight.objects.all())

    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'legacy_id', 'archival_reference_code', 'title', 'title_original', 'original_locale',
                  'contents_summary', 'contents_summary_original', 'date_from', 'date_to',
                  'time_start', 'time_end', 'note', 'note_original', 'access_rights', 'access_rights_restriction_date')
