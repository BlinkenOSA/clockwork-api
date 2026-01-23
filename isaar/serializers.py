from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from clockwork_api.fields.approximate_date_serializer_field import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from isaar.models import Isaar, IsaarParallelName, IsaarOtherName, IsaarStandardizedName, IsaarCorporateBodyIdentifier, \
    IsaarPlace, IsaarPlaceQualifier, IsaarRelationship


class IsaarOtherNameSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isaar.models.IsaarOtherName`.

    Used for representing and validating variant ("other") names associated with
    an ISAAR record. The parent ISAAR foreign key is excluded and is expected to
    be provided implicitly via nested writes.
    """

    class Meta:
        model = IsaarOtherName
        exclude = ('isaar',)


class IsaarParallelNameSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isaar.models.IsaarParallelName`.

    Parallel names are alternative authorized forms (often in other
    languages/scripts). The parent ISAAR foreign key is excluded and is expected
    to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsaarParallelName
        exclude = ('isaar',)


class IsaarStandardizedNameSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isaar.models.IsaarStandardizedName`.

    Standardized names represent normalized forms of the entity name according
    to a given standard. The parent ISAAR foreign key is excluded and is
    expected to be provided implicitly via nested writes.
    """

    class Meta:
        model = IsaarStandardizedName
        exclude = ('isaar',)


class IsaarCorporateBodyIdentifierSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isaar.models.IsaarCorporateBodyIdentifier`.

    Corporate body identifiers store internal or external identifiers for an
    ISAAR record. The parent ISAAR foreign key is excluded and is expected to be
    provided implicitly via nested writes.
    """

    class Meta:
        model = IsaarCorporateBodyIdentifier
        exclude = ('isaar',)


class IsaarPlaceQualifierSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isaar.models.IsaarPlaceQualifier`.

    Place qualifiers are controlled vocabulary values used to qualify place
    associations (e.g., headquarters, seat, place of activity).
    """

    class Meta:
        model = IsaarPlaceQualifier
        fields = '__all__'


class IsaarPlaceReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for :class:`isaar.models.IsaarPlace`.

    Expands the ``place_qualifier`` relationship into a nested
    :class:`IsaarPlaceQualifierSerializer` representation.
    """

    place_qualifier = IsaarPlaceQualifierSerializer()

    class Meta:
        model = IsaarPlace
        exclude = ('isaar',)


class IsaarPlaceWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for :class:`isaar.models.IsaarPlace`.

    Used for create/update operations where ``place_qualifier`` is expected to
    be provided as a primary key value (default ModelSerializer behavior). The
    parent ISAAR foreign key is excluded and is expected to be set implicitly
    via nested writes.
    """

    class Meta:
        model = IsaarPlace
        exclude = ('isaar',)


class IsaarListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing ISAAR authority records.

    Includes a read-only list of related ISAD reference codes via the reverse
    relation ``isad_set``.
    """

    isad = serializers.SlugRelatedField(many=True, slug_field='reference_code', read_only=True, source='isad_set')

    class Meta:
        model = Isaar
        fields = ['id', 'name', 'type', 'status', 'isad']


class IsaarReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for a full ISAAR record.

    Expands nested related data for names, identifiers, and places using the
    reverse relations:

        - ``isaarparallelname_set`` -> ``parallel_names``
        - ``isaarothername_set`` -> ``other_names``
        - ``isaarstandardizedname_set`` -> ``standardized_names``
        - ``isaarcorporatebodyidentifier_set`` -> ``corporate_body_identifiers``
        - ``isaarplace_set`` -> ``places``

    Notes
    -----
    This serializer uses ``fields = '__all__'`` for the ISAAR model and adds the
    expanded nested fields listed above.
    """

    parallel_names = IsaarParallelNameSerializer(many=True, source='isaarparallelname_set')
    other_names = IsaarOtherNameSerializer(many=True, source='isaarothername_set')
    standardized_names = IsaarStandardizedNameSerializer(many=True, source='isaarstandardizedname_set')
    corporate_body_identifiers = IsaarCorporateBodyIdentifierSerializer(
        many=True, source='isaarcorporatebodyidentifier_set'
    )
    places = IsaarPlaceReadSerializer(many=True, source='isaarplace_set')

    class Meta:
        model = Isaar
        fields = '__all__'


class IsaarWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Write serializer for an ISAAR record with nested create/update support.

    This serializer supports writable nested updates for repeatable ISAAR
    substructures (names, identifiers, places). Date fields are handled with
    :class:`~clockwork_api.fields.approximate_date_serializer_field.ApproximateDateSerializerField`
    to preserve approximate date semantics.

    Nested fields are written via reverse relations:

        - ``parallel_names`` -> ``isaarparallelname_set``
        - ``other_names`` -> ``isaarothername_set``
        - ``standardized_names`` -> ``isaarstandardizedname_set``
        - ``corporate_body_identifiers`` -> ``isaarcorporatebodyidentifier_set``
        - ``places`` -> ``isaarplace_set``
    """

    date_existence_from = ApproximateDateSerializerField()
    date_existence_to = ApproximateDateSerializerField()
    parallel_names = IsaarParallelNameSerializer(many=True, source='isaarparallelname_set', required=False)
    other_names = IsaarOtherNameSerializer(many=True, source='isaarothername_set', required=False)
    standardized_names = IsaarStandardizedNameSerializer(many=True, source='isaarstandardizedname_set', required=False)
    corporate_body_identifiers = IsaarCorporateBodyIdentifierSerializer(
        many=True, source='isaarcorporatebodyidentifier_set', required=False
    )
    places = IsaarPlaceWriteSerializer(many=True, source='isaarplace_set', required=False)

    class Meta:
        model = Isaar
        fields = '__all__'


class IsaarSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for selection lists and autocomplete UIs.

    Intended for lightweight payloads where only identity and basic status/type
    information are needed.
    """

    class Meta:
        model = Isaar
        fields = ('id', 'name', 'type', 'status')


class IsaarRelationshipSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`isaar.models.IsaarRelationship`.

    Provides the controlled relationship label used to qualify other name
    entries.
    """

    class Meta:
        model = IsaarRelationship
        fields = ('id', 'relationship')
