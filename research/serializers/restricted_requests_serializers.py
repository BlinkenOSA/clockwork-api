from rest_framework import serializers
from research.models import RequestItemPart


class RestrictedRequestsListSerializer(serializers.ModelSerializer):
    reference_code = serializers.SerializerMethodField()
    catalog_link = serializers.SerializerMethodField()
    request_date = serializers.SerializerMethodField()
    is_restricted = serializers.SerializerMethodField()
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True, source='request_item.request.researcher')
    research_subject = serializers.SerializerMethodField()
    motivation = serializers.SerializerMethodField()

    def get_reference_code(self, obj):
        return obj.finding_aids_entity.archival_reference_code

    def get_catalog_link(self, obj):
        return obj.finding_aids_entity.catalog_id

    def get_request_date(self, obj):
        return obj.request_item.request.request_date

    def get_is_restricted(self, obj):
        return obj.finding_aids_entity.access_rights.statement == 'Restricted'

    def get_research_subject(self, obj):
        if hasattr('restriction', obj.request_item):
            return obj.request_item.restriction.research_subject
        else:
            return "N/A"

    def get_motivation(self, obj):
        if hasattr('restriction', obj.request_item):
            return obj.request_item.restriction.motivation
        else:
            return "N/A"

    class Meta:
        model = RequestItemPart
        fields = ['id', 'finding_aids_entity', 'catalog_link', 'reference_code', 'request_date', 'researcher', 'research_subject',
                  'motivation', 'is_restricted', 'status']
