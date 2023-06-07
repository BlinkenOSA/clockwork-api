from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.models import AccessRight
from finding_aids.models import FindingAidsEntity


class FindingAidsGridSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    access_rights = serializers.SlugRelatedField(slug_field='statement', queryset=AccessRight.objects.all())

    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'title', 'title_original', 'original_locale',
                  'contents_summary', 'contents_summary_original', 'date_from', 'date_to',
                  'time_start', 'time_end', 'note', 'note_original', 'access_rights', 'access_rights_restriction_date')
