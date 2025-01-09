from rest_framework import serializers
from research.models import RequestItemPart


class RestrictedRequestsListSerializer(serializers.ModelSerializer):
    reference_code = serializers.SerializerMethodField()
    request_date = serializers.SerializerMethodField()
    is_restricted = serializers.SerializerMethodField()
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True, source='request_item.request.researcher')

    def get_reference_code(self, obj):
        return obj.finding_aids_entity.archival_reference_code

    def get_request_date(self, obj):
        return obj.request_item.request.request_date

    def get_is_restricted(self, obj):
        return obj.finding_aids_entity.access_rights.statement == 'Restricted'

    class Meta:
        model = RequestItemPart
        fields = ['finding_aids_entity', 'reference_code', 'request_date', 'researcher', 'is_restricted', 'status']
