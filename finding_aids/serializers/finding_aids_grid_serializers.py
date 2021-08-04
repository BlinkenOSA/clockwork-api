from drf_writable_nested import WritableNestedModelSerializer
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from finding_aids.models import FindingAidsEntity


class FindingAidsGridSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = '__all__'
