from drf_writable_nested import WritableNestedModelSerializer
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from finding_aids.models import FindingAidsEntity


class FindingAidsGridSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'title', 'title_original', 'original_locale',
                  'contents_summary', 'contents_summary_original', 'date_from', 'date_to',
                  'time_start', 'time_end', 'note', 'note_original')
