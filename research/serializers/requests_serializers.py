from django.db.models import Q
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from container.models import Container
from finding_aids.models import FindingAidsEntity
from research.models import RequestItem, Request, RequestItemPart, RequestedMaterialsSharePointJob


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
    is_missing = serializers.SerializerMethodField()

    def get_reference_code(self, obj):
        """
        Returns the archival reference code of the linked finding aids entity.
        """
        return obj.finding_aids_entity.archival_reference_code

    def get_is_restricted(self, obj):
        """
        Returns True if the linked finding aids entity is restricted.
        """
        return bool(
            obj.finding_aids_entity.access_rights and
            obj.finding_aids_entity.access_rights.statement == 'Restricted'
        )

    def get_is_missing(self, obj):
        """
        Returns True if the linked finding aids entity is missing.
        """
        return obj.finding_aids_entity.missing

    class Meta:
        model = RequestItemPart
        fields = ['finding_aids_entity', 'reference_code', 'is_restricted', 'is_missing', 'status']


class RequestItemListSerializer(serializers.ListSerializer):
    """Batch the cross-request status lookup used by the MLR column."""

    def to_representation(self, data):
        items = list(data.all() if hasattr(data, 'all') else data)
        container_ids = {item.container_id for item in items if item.item_origin == 'FA' and item.container_id}
        identifiers = {
            item.identifier for item in items
            if item.item_origin != 'FA' and item.identifier
        }

        candidate_filter = Q()
        if container_ids:
            candidate_filter |= Q(item_origin='FA', container_id__in=container_ids)
        if identifiers:
            candidate_filter |= ~Q(item_origin='FA') & Q(identifier__in=identifiers)

        archival_items = {}
        library_items = {}
        if candidate_filter.children:
            candidates = RequestItem.objects.filter(candidate_filter).values(
                'id', 'item_origin', 'container_id', 'identifier', 'status'
            )
            for candidate in candidates:
                if candidate['item_origin'] == 'FA':
                    archival_items.setdefault(candidate['container_id'], []).append(candidate)
                else:
                    library_items.setdefault(candidate['identifier'], []).append(candidate)

        status_cache = {}
        for item in items:
            candidates = (
                archival_items.get(item.container_id, [])
                if item.item_origin == 'FA'
                else library_items.get(item.identifier, [])
            )
            statuses = {candidate['status'] for candidate in candidates if candidate['id'] != item.id}
            status_cache[item.id] = {
                'pending': bool(statuses.intersection({'1', '2'})),
                'in_use': '3' in statuses,
                'returned': '4' in statuses,
            }

        self.child.other_request_statuses = status_cache
        return super().to_representation(items)


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
        Derived from the linked container or specifically requested finding-aids entities.
    parts
        Serialized list of :class:`RequestItemPart` entries linked to the request item.
    """

    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True, source='request.researcher')
    researcher_id = serializers.IntegerField(source='request.researcher_id', read_only=True)
    researcher_email = serializers.SlugRelatedField(slug_field='email', read_only=True, source='request.researcher')
    created_date = serializers.SlugRelatedField(slug_field='created_date', read_only=True, source='request')
    request_date = serializers.SlugRelatedField(slug_field='request_date', read_only=True, source='request')
    requested_materials_shared_date = serializers.DateTimeField(
        source='request.requested_materials_shared_date',
        read_only=True,
    )
    carrier_type = serializers.SlugRelatedField(slug_field='type', read_only=True, source='container.carrier_type')
    archival_reference_number = serializers.SerializerMethodField()
    mlr = serializers.SerializerMethodField()
    has_restricted_content = serializers.SerializerMethodField()
    research_allowed = serializers.SerializerMethodField()
    has_digital_version = serializers.SerializerMethodField()
    digital_version_barcode = serializers.SerializerMethodField()
    requested_materials_prepared = serializers.SerializerMethodField()
    parts = RequestItemPartSerializer(source='requestitempart_set', many=True)

    def get_mlr(self, obj):
        """
        Returns a display string indicating item location/availability.

        Behavior depends on origin:

        - Finding Aids (FA):
            - If another request item for the same container is available (status '1' or '2'):
                returns ``'Appears in another request'``.
            - If another request item for the same container is currently processed (status '3'):
                returns ``'Currently used'``.
            - If another request item for the same container is returned (status '4'):
                returns ``'Waiting to be reshelved'``.
            - Otherwise tries to resolve MRSS locations from the MLR.

        - Non-FA (library / film):
            - Checks other request items with the same identifier for usage/return state.
            - Otherwise returns ``'Library Record'``.
        """
        status_info = getattr(self, 'other_request_statuses', {}).get(obj.id)
        if status_info is None:
            if obj.item_origin == 'FA':
                matching_items = RequestItem.objects.filter(
                    item_origin='FA', container=obj.container
                ).exclude(id=obj.id)
            else:
                matching_items = RequestItem.objects.filter(
                    identifier=obj.identifier
                ).exclude(id=obj.id).exclude(item_origin='FA')
            statuses = set(matching_items.values_list('status', flat=True))
            status_info = {
                'pending': bool(statuses.intersection({'1', '2'})),
                'in_use': '3' in statuses,
                'returned': '4' in statuses,
            }

        appears_in_another_request = status_info['pending']
        if status_info['in_use']:
            return 'Currently used'
        if status_info['returned']:
            return 'Waiting to be reshelved'

        if obj.item_origin == 'FA':
            if obj.container:
                series = obj.container.archival_unit
                carrier_type = obj.container.carrier_type
                mlr = next((
                    record for record in series.mlrentity_set.all()
                    if record.carrier_type_id == carrier_type.id
                ), None)
                if mlr:
                    return {
                        'locations': mlr.get_locations(),
                        'another_request': appears_in_another_request
                    }
                return ''
            else:
                return ''

        return 'Library Record'

    def get_has_restricted_content(self, obj):
        """
        Returns True if any Finding Aids entities in the requested container is restricted.
        """
        annotated_value = getattr(obj, 'container_has_restricted_content', None)
        if annotated_value is not None:
            return annotated_value
        return FindingAidsEntity.objects.filter(
            container=obj.container,
            access_rights__statement='Restricted'
        ).exists()

    def get_research_allowed(self, obj):
        """
        Determines whether research is allowed for the request item.

        Logic summary:
            - If all parts are not restricted: allowed.
            - If there are some not restricted and no parts in 'new' status: allowed.
            - If at least one part is approved (approved/approved_on_site) and no parts are 'new': allowed.
            - If all parts are 'rejected': allowed.
            - Otherwise: not allowed.

        Returns
        -------
        bool
            True if research should be allowed, otherwise False.
        """
        annotated_counts = (
            'request_part_count',
            'unrestricted_request_part_count',
            'new_request_part_count',
            'approved_request_part_count',
            'rejected_request_part_count',
        )
        if all(hasattr(obj, field) for field in annotated_counts):
            count_total = obj.request_part_count
            count_not_restricted = obj.unrestricted_request_part_count
            count_new = obj.new_request_part_count
            count_approved = obj.approved_request_part_count
            count_rejected = obj.rejected_request_part_count
        else:
            count_total = obj.requestitempart_set.count()
            count_not_restricted = obj.requestitempart_set.filter(
                finding_aids_entity__access_rights__statement='Not restricted'
            ).count()
            count_new = obj.requestitempart_set.filter(status='new').count()
            count_approved = obj.requestitempart_set.filter(
                status__in=('approved', 'approved_on_site')
            ).count()
            count_rejected = obj.requestitempart_set.filter(status='rejected').count()

        # If all the records are not restricted
        if count_not_restricted == count_total:
            return True

        if count_not_restricted > 0 and count_new == 0:
            return True

        # If there is at least one approved and no new one
        if count_approved > 0 and count_new == 0:
            return True

        # If all the records are rejected (this way the status of the request is already 'Returned')
        if count_rejected == count_total:
            return True

        return False

    def get_has_digital_version(self, obj):
        """
        Returns True if the linked container or one of the specifically
        requested finding-aids entities has a digital version.
        """
        if obj.container and obj.container.digital_version_exists:
            return True
        annotation_names = (
            'container_entity_has_digital',
            'container_has_digital_record',
            'requested_entity_has_digital',
        )
        annotated_values = [getattr(obj, name, None) for name in annotation_names]
        if all(value is not None for value in annotated_values):
            return any(annotated_values)

        return bool(obj.container and obj.container.has_digital_version) or FindingAidsEntity.objects.filter(
            requestitempart__request_item=obj,
        ).filter(
            Q(digital_version_exists=True) | Q(digital_versions__isnull=False)
        ).exists()

    def get_digital_version_barcode(self, obj):
        """
        Returns the container barcode when available. For a part-level-only
        digital version, returns the finding-aids reference code instead.
        """
        if obj.container and self.get_has_digital_version(obj):
            return obj.container.barcode

        reference_codes = {
            part.finding_aids_entity.archival_reference_code
            for part in obj.requestitempart_set.all()
            if part.finding_aids_entity.digital_version_exists or
            bool(list(part.finding_aids_entity.digital_versions.all()))
        }

        return ', '.join(sorted(filter(None, reference_codes))) or None

    def get_requested_materials_prepared(self, obj):
        return any(job.status == 'completed' for job in obj.requested_materials_jobs.all())

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
        list_serializer_class = RequestItemListSerializer


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
        fields = ('id', 'item_origin', 'container', 'identifier', 'other_identifier', 'library_id', 'title')


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
                  'other_identifier', 'title', 'quantity', 'served_date')


class RequestItemWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a request item.

    Intended for edit forms where a subset of request item fields is writable.
    """

    class Meta:
        model = RequestItem
        fields = ('id', 'item_origin', 'container', 'identifier', 'other_identifier', 'title', 'quantity')


class RequestedMaterialsSharePointJobSerializer(serializers.ModelSerializer):
    """
    Serializer for requested-materials SharePoint preparation jobs.
    """

    request_id = serializers.IntegerField(source='request_item.request.id', read_only=True)
    request_item_id = serializers.IntegerField(source='request_item.id', read_only=True)
    progress_percent = serializers.SerializerMethodField()

    def get_progress_percent(self, obj):
        if obj.status == 'completed':
            return 100
        if obj.progress_total:
            return int((obj.progress_current / obj.progress_total) * 100)
        return 0

    class Meta:
        model = RequestedMaterialsSharePointJob
        fields = (
            'id',
            'request_id',
            'request_item_id',
            'status',
            'current_step',
            'message',
            'progress_current',
            'progress_total',
            'progress_percent',
            'celery_task_id',
            'result',
            'error_message',
            'created_date',
            'started_date',
            'finished_date',
        )
