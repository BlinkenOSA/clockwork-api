from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accession.models import Accession, AccessionItem, AccessionMethod, AccessionCopyrightStatus
from archival_unit.serializers import ArchivalUnitSelectSerializer, ArchivalUnitReadSerializer
from clockwork_api.fields.approximate_date_serializer_field import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin


class AccessionMethodSelectSerializer(serializers.ModelSerializer):
    """
    Serializer for selecting an accession method.

    Used typically for dropdown lists or foreign key selection fields
    where all fields of the AccessionMethod model are required.
    """
    class Meta:
        model = AccessionMethod
        fields = '__all__'


class AccessionCopyrightStatusSelectSerializer(serializers.ModelSerializer):
    """
    Serializer for selecting a copyright status.

    Returns all fields of AccessionCopyrightStatus, often used in UI select lists.
    """
    class Meta:
        model = AccessionCopyrightStatus
        fields = '__all__'


class AccessionItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual accession items (e.g., boxes or folders).

    Represents quantity, container type, and optional content description.
    Used on the Accession Form to manage items within an accession.
    """
    class Meta:
        model = AccessionItem
        fields = 'id', 'quantity', 'container', 'content'


class AccessionReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for accession details, including nested items.

    Includes:
        - All Accession fields
        - A nested list of AccessionItem records via accessionitem_set
    """
    items = AccessionItemSerializer(many=True, source='accessionitem_set')

    class Meta:
        model = Accession
        fields = '__all__'


class AccessionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views of accessions.

    Includes only the primary identifying fields used in table or list views.
    """
    archival_unit = ArchivalUnitReadSerializer()

    class Meta:
        model = Accession
        fields = ['id', 'seq', 'transfer_date', 'title', 'archival_unit']


class AccessionWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Serializer for creating or updating accessions, including nested items.

    Handles:
        - Approximate date fields
        - Nested accession items (WritableNestedModelSerializer)
        - Validation of creation_date_from <= creation_date_to
        - User data injection via UserDataSerializerMixin
    """
    transfer_date = ApproximateDateSerializerField()
    creation_date_from = ApproximateDateSerializerField(required=False)
    creation_date_to = ApproximateDateSerializerField(required=False)
    items = AccessionItemSerializer(many=True, source='accessionitem_set')

    def validate(self, data):
        """
        Validates that the creation date range is chronological.

        Args:
            data: Incoming serializer data.

        Raises:
            ValidationError: If creation_date_from > creation_date_to.

        Returns:
            The validated data dictionary.
        """
        creation_date_from = data.get('creation_date_from', None)
        creation_date_to = data.get('creation_date_to', None)
        if creation_date_to:
            if creation_date_from > creation_date_to:
                raise ValidationError("Date from value is bigger than date to value.")
        return data

    class Meta:
        model = Accession
        fields = '__all__'


class AccessionSelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer used for dropdown/select boxes.

    Includes minimal identifying metadata such as:
        - transfer_date
        - sequence number
        - linked Archival Unit info
        - legacy Archival Unit data
    """
    archival_unit = ArchivalUnitSelectSerializer()

    class Meta:
        model = Accession
        fields = ('id', 'transfer_date', 'seq',
                  'archival_unit', 'archival_unit_legacy_number', 'archival_unit_legacy_name')