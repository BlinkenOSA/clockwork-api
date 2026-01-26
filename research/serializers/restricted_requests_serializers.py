from rest_framework import serializers
from research.models import RequestItemPart


class RestrictedRequestsListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing restricted request items.

    This serializer is used in restricted-material review workflows and
    aggregates information from:
        - the linked finding aids entity,
        - the parent request and researcher,
        - the associated restriction form (if present).

    It provides archivists with the contextual data needed to evaluate
    access requests for restricted materials.
    """

    reference_code = serializers.SerializerMethodField()
    catalog_link = serializers.SerializerMethodField()
    request_date = serializers.SerializerMethodField()
    is_restricted = serializers.SerializerMethodField()
    researcher = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
        source='request_item.request.researcher'
    )
    research_subject = serializers.SerializerMethodField()
    motivation = serializers.SerializerMethodField()

    def get_reference_code(self, obj):
        """
        Returns the archival reference code of the linked finding aids entity.
        """
        return obj.finding_aids_entity.archival_reference_code

    def get_catalog_link(self, obj):
        """
        Returns the catalog identifier of the linked finding aids entity.
        """
        return obj.finding_aids_entity.catalog_id

    def get_request_date(self, obj):
        """
        Returns the request date of the parent request.
        """
        return obj.request_item.request.request_date

    def get_is_restricted(self, obj):
        """
        Returns True if the linked finding aids entity is restricted.
        """
        return obj.finding_aids_entity.access_rights.statement == 'Restricted'

    def get_research_subject(self, obj):
        """
        Returns the declared research subject from the restriction form.

        Returns ``"N/A"`` if no restriction record exists.
        """
        if hasattr(obj.request_item, 'restriction'):
            return obj.request_item.restriction.research_subject
        else:
            return "N/A"

    def get_motivation(self, obj):
        """
        Returns the research motivation from the restriction form.

        Returns ``"N/A"`` if no restriction record exists.
        """
        if hasattr(obj.request_item, 'restriction'):
            return obj.request_item.restriction.motivation
        else:
            return "N/A"

    class Meta:
        model = RequestItemPart
        fields = [
            'id',
            'finding_aids_entity',
            'catalog_link',
            'reference_code',
            'request_date',
            'researcher',
            'research_subject',
            'motivation',
            'is_restricted',
            'status',
        ]
