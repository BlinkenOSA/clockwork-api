from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.isad_archival_unit_serializer_mixin import IsadArchivalUnitSerializerMixin
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import CarrierTypeSelectSerializer, ExtentUnitSelectSerializer
from isad.models import Isad, IsadCreator, IsadCarrier, IsadExtent, IsadLocationOfOriginals, IsadLocationOfCopies, \
    IsadRelatedFindingAids


class IsadCreatorSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isad.models.IsadCreator`.

    Used for representing and validating free-text creator entries associated
    with an ISAD record. The parent ISAD foreign key is excluded and is expected
    to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsadCreator
        exclude = ('isad',)


class IsadCarrierSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isad.models.IsadCarrier`.

    Used for representing and validating carrier count/type entries associated
    with an ISAD record. The parent ISAD foreign key is excluded and is expected
    to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsadCarrier
        exclude = ('isad',)


class IsadExtentSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isad.models.IsadExtent`.

    Used for representing and validating extent entries associated with an ISAD
    record, including the controlled extent unit and the numeric value. The
    parent ISAD foreign key is excluded and is expected to be provided
    implicitly via nested writes.
    """

    class Meta:
        model = IsadExtent
        exclude = ('isad',)


class IsadLocationOfOriginalsSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isad.models.IsadLocationOfOriginals`.

    Used for representing and validating location-of-originals entries
    associated with an ISAD record. The parent ISAD foreign key is excluded and
    is expected to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsadLocationOfOriginals
        exclude = ('isad',)


class IsadLocationOfCopiesSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isad.models.IsadLocationOfCopies`.

    Used for representing and validating location-of-copies entries associated
    with an ISAD record. The parent ISAD foreign key is excluded and is expected
    to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsadLocationOfCopies
        exclude = ('isad',)


class IsadRelatedFindingAidsSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isad.models.IsadRelatedFindingAids`.

    Used for representing and validating related finding aids entries
    associated with an ISAD record. The parent ISAD foreign key is excluded and
    is expected to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsadRelatedFindingAids
        exclude = ('isad',)


class IsadReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for a full ISAD record.

    Expands nested related data for repeatable structures using reverse
    relations:

        - ``isadcreator_set`` -> ``creators``
        - ``isadcarrier_set`` -> ``carriers``
        - ``isadextent_set`` -> ``extents``
        - ``isadrelatedfindingaids_set`` -> ``related_finding_aids``
        - ``isadlocationoforiginals_set`` -> ``location_of_originals``
        - ``isadlocationofcopies_set`` -> ``location_of_copies``

    Also exposes ``title_full`` derived from the linked archival unit.
    """

    creators = IsadCreatorSerializer(many=True, source='isadcreator_set')
    carriers = IsadCarrierSerializer(many=True, source='isadcarrier_set')
    extents = IsadExtentSerializer(many=True, source='isadextent_set')
    related_finding_aids = IsadRelatedFindingAidsSerializer(many=True, source='isadrelatedfindingaids_set')
    location_of_originals = IsadLocationOfOriginalsSerializer(many=True, source='isadlocationoforiginals_set')
    location_of_copies = IsadLocationOfCopiesSerializer(many=True, source='isadlocationofcopies_set')
    title_full = serializers.SerializerMethodField()

    def get_title_full(self, obj):
        """
        Returns the full archival unit title for display purposes.
        """
        return obj.archival_unit.title_full

    class Meta:
        model = Isad
        fields = '__all__'


class IsadWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Write serializer for an ISAD record with nested create/update support.

    Supports writable nested updates for repeatable ISAD substructures (creators,
    carriers, extents, and related materials/locations). User provenance fields
    are handled via :class:`clockwork_api.mixins.user_data_serializer_mixin.UserDataSerializerMixin`.

    Nested fields are written via reverse relations:

        - ``creators`` -> ``isadcreator_set``
        - ``carriers`` -> ``isadcarrier_set``
        - ``extents`` -> ``isadextent_set``
        - ``related_finding_aids`` -> ``isadrelatedfindingaids_set``
        - ``location_of_originals`` -> ``isadlocationoforiginals_set``
        - ``location_of_copies`` -> ``isadlocationofcopies_set``
    """

    creators = IsadCreatorSerializer(many=True, source='isadcreator_set', required=False)
    carriers = IsadCarrierSerializer(many=True, source='isadcarrier_set', required=False)
    extents = IsadExtentSerializer(many=True, source='isadextent_set', required=False)
    related_finding_aids = IsadRelatedFindingAidsSerializer(
        many=True, source='isadrelatedfindingaids_set', required=False
    )
    location_of_originals = IsadLocationOfOriginalsSerializer(
        many=True, source='isadlocationoforiginals_set', required=False
    )
    location_of_copies = IsadLocationOfCopiesSerializer(
        many=True, source='isadlocationofcopies_set', required=False
    )

    class Meta:
        model = Isad
        fields = '__all__'


class IsadSeriesSerializer(IsadArchivalUnitSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for series-level archival units within the ISAD tree view.

    This serializer is used to represent :class:`archival_unit.models.ArchivalUnit`
    objects at level ``S`` (Series), including their related ISAD record and a
    computed status field provided by :class:`IsadArchivalUnitSerializerMixin`.
    """

    status = serializers.SerializerMethodField()

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'isad', 'fonds', 'subfonds', 'series', 'level', 'reference_code', 'title', 'status')


class IsadSubfondsSerializer(IsadArchivalUnitSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for subfonds-level archival units within the ISAD tree view.

    Provides a ``children`` field that returns series-level children, optionally
    restricted to the requesting user's allowed archival units.
    """

    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_children(self, obj):
        """
        Returns series-level children for the given subfonds archival unit.

        If the requesting user has an allow-list (``user.user_profile.allowed_archival_units``),
        children are restricted to the allowed series under the fonds/subfonds.
        Otherwise, the archival unit's direct children are returned.

        Returns
        -------
        list or None
            Serialized list of series children, or None if there are no children.
        """
        user = self.context['user']
        if user.user_profile.allowed_archival_units.count() > 0:
            queryset = ArchivalUnit.objects.none()
            for archival_unit in user.user_profile.allowed_archival_units.filter(
                fonds=obj.fonds, subfonds=obj.subfonds
            ):
                queryset |= ArchivalUnit.objects.filter(
                    fonds=archival_unit.fonds,
                    subfonds=archival_unit.subfonds,
                    series=archival_unit.series,
                    level='S')
            return IsadSeriesSerializer(queryset, many=True, context=self.context).data
        else:
            if obj.children.count() > 0:
                return IsadSeriesSerializer(obj.children, many=True, context=self.context).data
            else:
                return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'isad', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'status')


class IsadFondsSerializer(IsadArchivalUnitSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for fonds-level archival units within the ISAD tree view.

    Provides a ``children`` field that returns subfonds-level children, optionally
    restricted to the requesting user's allowed archival units.
    """

    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_children(self, obj):
        """
        Returns subfonds-level children for the given fonds archival unit.

        If the requesting user has an allow-list (``user.user_profile.allowed_archival_units``),
        children are restricted to the allowed subfonds under the fonds.
        Otherwise, the archival unit's direct children are returned.

        Returns
        -------
        list or None
            Serialized list of subfonds children, or None if there are no children.
        """
        user = self.context['user']
        if user.user_profile.allowed_archival_units.count() > 0:
            queryset = ArchivalUnit.objects.none()
            for archival_unit in user.user_profile.allowed_archival_units.filter(fonds=obj.fonds):
                queryset |= ArchivalUnit.objects.filter(
                    fonds=archival_unit.fonds,
                    subfonds=archival_unit.subfonds,
                    level='SF')
            return IsadSubfondsSerializer(queryset, many=True, context=self.context).data
        else:
            if obj.children.count() > 0:
                return IsadSubfondsSerializer(obj.children, many=True, context=self.context).data
            else:
                return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'isad', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'status')


class IsadPreCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used to prefill ISAD creation forms from an archival unit.

    Maps an :class:`archival_unit.models.ArchivalUnit` to a minimal payload that
    includes the archival unit identifier and basic descriptive fields expected
    by ISAD creation workflows.
    """

    archival_unit = serializers.SerializerMethodField()
    description_level = serializers.CharField(source='level')

    def get_archival_unit(self, obj):
        """
        Returns the archival unit primary key in the field expected by the client.
        """
        return obj.id

    class Meta:
        model = ArchivalUnit
        fields = ('archival_unit', 'reference_code', 'title', 'description_level')


class IsadSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for selecting ISAD records.

    Intended for lightweight payloads in selection lists or autocomplete
    components.
    """

    class Meta:
        model = Isad
        fields = ('id', 'reference_code', 'title', 'published')
