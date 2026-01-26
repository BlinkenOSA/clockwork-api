from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from container.models import Container
from mlr.models import MLREntity
from research.models import RequestItem, Request, RequestItemPart


class RequestItemPartSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`research.models.RequestItemPart`.

    Exposes part-level restricted-content metadata derived from the linked
    finding aids entity, including:
        - the archival reference code of the finding aids entity
        - whether the linked entity is restricted
        - the current part workflow status
    """

    reference_code = serializers.SerializerMethodField()
    is_restricted = serializers.SerializerMethodField()

    def get_reference_code(self, obj):
        """
        Returns the archival reference code of the linked finding aids entity.
        """
        return obj.finding_aids_entity.archival_reference_code

    def get_is_restricted(self, obj):
        """
        Returns True if the linked finding aids entity is restricted.
        """
        return obj.finding_aids_entity.access_rights.statement == 'Restricted'

    class Meta:
        model = RequestItemPart
        fields = ['finding_aids_entity', 'reference_code', 'is_restricted', 'status']


class RequestListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing request items with enriched display fields.

    This serializer is built on :class:`research.models.RequestItem` but exposes
    additional fields sourced from the parent request/researcher, container,
    MLR, and part-level restriction workflow.

    Derived fields
    -------------
    researcher / researcher_email
        Sourced from the parent request's researcher.
    created_date / request_date
        Sourced from the parent request.
    carrier_type
        Sourced from the linked container's carrier type.
    archival_reference_number
        Human-readable archival unit reference + container number for finding aids items.
    mlr
        Location or availability information, based on origin and current usage.
    has_restricted_content
        True if any linked parts reference restricted finding aids entities.
    research_allowed
        True if the set of parts permits research (based on restriction statuses).
    has_digital_version / digital_version_barcode
        Derived from the linked container when applicable.
    parts
        Serialized list of :class:`RequestItemPart` entries linked to the request item.
    """

    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True, source='request.researcher')
    researcher_email = serializers.SlugRelatedField(slug_field='email', read_only=True, source='request.researcher')
    created_date = serializers.SlugRelatedField(slug_field='created_date', read_only=True, source='request')
    request_date = serializers.SlugRelatedField(slug_field='request_date', read_only=True, source='request')
    carrier_type = serializers.SlugRelatedField(slug_field='type', read_only=True, source='container.carrier_type')
    archival_reference_number = serializers.SerializerMethodField()
    mlr = serializers.SerializerMethodField()
    has_restricted_content = serializers.SerializerMethodField()
    research_allowed = serializers.SerializerMethodField()
    has_digital_version = serializers.SerializerMethodField()
    digital_version_barcode = serializers.SerializerMethodField()
    parts = RequestItemPartSerializer(source='requestitempart_set', many=True)

    def get_mlr(self, obj):
        """
        Returns a display string indicating item location/availability.

        Behavior depends on origin:

        - Finding Aids (FA):
            - If another request item for the same container is currently processed (status '3'):
                returns ``'Currently used'``.
            - If another request item for the same container is returned (status '4'):
                returns ``'Waiting to be reshelved'``.
            - Otherwise tries to resolve MRSS locations from the MLR.

        - Non-FA (library / film):
            - Checks other request items with the same identifier for usage/return state.
            - Otherwise returns ``'Library Record'``.
        """
        if obj.item_origin == 'FA':
            same_archival_request = RequestItem.objects.filter(
                item_origin='FA', container=obj.container).exclude(id=obj.id)
            if same_archival_request.filter(status='3').exists():
                return 'Currently used'
            if same_archival_request.filter(status='4').exists():
                return 'Waiting to be reshelved'

        else:
            same_library_request = RequestItem.objects.filter(
                identifier=obj.identifier).exclude(id=obj.id, item_origin='FA')
            if same_library_request.filter(status='3').exists():
                return 'Currently used'
            if same_library_request.filter(status='4').exists():
                return 'Waiting to be reshelved'

        if obj.item_origin == 'FA':
            if obj.container:
                series = obj.container.archival_unit
                carrier_type = obj.container.carrier_type
                try:
                    mlr = MLREntity.objects.get(series=series, carrier_type=carrier_type)
                    return mlr.get_locations()
                except ObjectDoesNotExist:
                    return ''
            else:
                return ''

        return 'Library Record'

    def get_has_restricted_content(self, obj):
        """
        Returns True if any linked parts are restricted.
        """
        return obj.requestitempart_set.filter(finding_aids_entity__access_rights__statement='Restricted').count() > 0

    def get_research_allowed(self, obj):
        """
        Determines whether research is allowed for the request item.

        Logic summary:
            - If all parts are not restricted: allowed.
            - If there are some not restricted and no parts in 'new' status: allowed.
            - If at least one part is approved (approved/approved_on_site) and no parts are 'new': allowed.
            - Otherwise: not allowed.

        Returns
        -------
        bool
            True if research should be allowed, otherwise False.
        """
        count_total = obj.requestitempart_set.count()
        count_not_restricted = obj.requestitempart_set.filter(
            finding_aids_entity__access_rights__statement='Not restricted'
        ).count()
        count_new = obj.requestitempart_set.filter(Q(status='new')).count()
        count_approved = obj.requestitempart_set.filter(Q(status='approved') | Q(status='approved_on_site')).count()

        # If all the records are not restricted
        if count_not_restricted == count_total:
            return True

        if count_not_restricted > 0 and count_new == 0:
            return True

        # If there is at least one approved and no new one
        if count_approved > 0 and count_new == 0:
            return True

        return False

    def get_has_digital_version(self, obj):
        """
        Returns True if the linked container has a digital version.
        """
        if obj.container:
            return obj.container.digital_version_exists
        else:
            return False

    def get_digital_version_barcode(self, obj):
        """
        Returns the container barcode when a digital version exists.
        """
        if obj.container:
            if obj.container.has_digital_version:
                return obj.container.barcode
            else:
                return None

    def get_archival_reference_number(self, obj):
        """
        Returns a formatted archival reference number for finding aids items.

        Returns
        -------
        str
            ``"<archival_unit_reference_code>:<container_no>"`` for FA items with
            a container; ``"Unknown(?)"`` for FA items without a container; empty
            string otherwise.
        """
        if obj.item_origin == 'FA':
            if obj.container:
                return "%s:%s" % (obj.container.archival_unit.reference_code, obj.container.container_no)
            else:
                return 'Unknown(?)'
        else:
            return ''

    class Meta:
        model = RequestItem
        fields = '__all__'


class ContainerListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing containers in selection endpoints.

    Exposes a single computed ``container_label`` in the format:
    ``"<container_no> (<carrier_type>)"``.
    """

    container_label = serializers.SerializerMethodField()

    def get_container_label(self, obj):
        """
        Returns the label used by container selection UIs.
        """
        return "%s (%s)" % (obj.container_no, obj.carrier_type.type)

    class Meta:
        model = Container
        fields = ('id', 'container_label')


class RequestItemCreateSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for creating request items as part of nested request creation.
    """

    class Meta:
        model = RequestItem
        fields = ('id', 'item_origin', 'container', 'identifier', 'library_id', 'title')


class RequestCreateSerializer(WritableNestedModelSerializer):
    """
    Serializer for creating a request with nested request items.

    Uses :class:`drf_writable_nested.WritableNestedModelSerializer` to create a
    :class:`research.models.Request` together with its ``requestitem_set``.
    """

    request_items = RequestItemCreateSerializer(many=True, source='requestitem_set')

    class Meta:
        model = Request
        fields = ('researcher', 'request_date', 'request_items')


class RequestItemReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading a request item in edit/detail contexts.

    Provides lightweight, UI-friendly representations of related objects:
        - researcher name
        - request date
        - archival unit label/value (from container)
        - container label/value (from container)
    """

    researcher = serializers.CharField(source='request.researcher.name', read_only=True)
    request_date = serializers.CharField(source='request.request_date', read_only=True)
    archival_unit = serializers.SerializerMethodField()
    container = serializers.SerializerMethodField()

    def get_archival_unit(self, obj):
        """
        Returns a label/value payload for the linked archival unit (via container).
        """
        if obj.container:
            return {
                'label': obj.container.archival_unit.reference_code,
                'value': obj.container.archival_unit.id
            }

    def get_container(self, obj):
        """
        Returns a label/value payload for the linked container.
        """
        if obj.container:
            return {
                'label': "%s (%s)" % (obj.container.container_no, obj.container.carrier_type.type),
                'value': obj.container.id
            }

    class Meta:
        model = RequestItem
        fields = ('id', 'researcher', 'request_date', 'item_origin', 'archival_unit', 'container', 'identifier',
                  'title', 'quantity')


class RequestItemWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a request item.

    Intended for edit forms where a subset of request item fields is writable.
    """

    class Meta:
        model = RequestItem
        fields = ('id', 'item_origin', 'container', 'identifier', 'title', 'quantity')
