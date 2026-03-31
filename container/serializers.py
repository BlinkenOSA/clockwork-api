import json
import datetime
from rest_framework import serializers

from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from container.models import Container
from controlled_list.models import CarrierType
from digitization.models import DigitalVersion, DigitalVersionPhysicalCopy
from finding_aids.models import FindingAidsEntity

class ContainerDigitalVersionPhysicalCopySerializer(serializers.ModelSerializer):
    """
    Serializer for physical copies of digital versions associated with a container.
    """

    class Meta:
        model = DigitalVersionPhysicalCopy
        fields = '__all__'


class ContainerDigitalVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for digital versions associated with a container.
    """

    physical_copies = ContainerDigitalVersionPhysicalCopySerializer(many=True, read_only=True)

    class Meta:
        model = DigitalVersion
        fields = '__all__'


class ContainerReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for containers.

    This serializer exposes all container fields for retrieval and internal
    read operations where full model state is needed.
    """

    digital_versions = ContainerDigitalVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Container
        fields = '__all__'


class ContainerWriteSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Write serializer for containers.

    Excludes fields that are system-managed:
        - container_no: assigned automatically on initial save
        - digital_version_creation_date: set automatically when a digital
          version is marked as existing and no date is provided

    This serializer also applies user metadata behavior via UserDataSerializerMixin.
    """

    class Meta:
        model = Container
        exclude = ('container_no', 'digital_version_creation_date')


class ContainerListSerializer(serializers.ModelSerializer):
    """
    List serializer for containers.

    Provides a compact representation suitable for list views, including:
        - a human-readable carrier type
        - a computed reference code
        - counts of related finding-aid entities (total and published)

    Counts exclude template entities.
    """

    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    reference_code = serializers.SerializerMethodField(source='container_no')
    total_number = serializers.SerializerMethodField()
    total_published_number = serializers.SerializerMethodField()
    digital_versions_masters = serializers.SerializerMethodField()
    digital_versions_access_copies = serializers.SerializerMethodField()
    digital_versions_in_finding_aids = serializers.SerializerMethodField()

    def get_total_number(self, obj):
        """
        Returns the number of non-template finding-aid entities in the container.
        """
        return FindingAidsEntity.objects.filter(container=obj).exclude(is_template=True).count()

    def get_total_published_number(self, obj):
        """
        Returns the number of published, non-template finding-aid entities in the container.
        """
        return FindingAidsEntity.objects.filter(container=obj, published=True).exclude(is_template=True).count()

    def get_reference_code(self, obj):
        """
        Builds the container reference code used in list displays.

        Format:
            <archival_unit.reference_code>:<container_no>
        """
        return "%s:%s" % (obj.archival_unit.reference_code, obj.container_no)

    def get_digital_versions_masters(self, obj):
        """
        Returns the count of master digital versions associated with the container.
        """
        return DigitalVersion.objects.filter(container=obj, finding_aids_entity__isnull=True, level='M').count()

    def get_digital_versions_access_copies(self, obj):
        """
        Returns the count of access copy digital versions associated with the container.
        """
        return DigitalVersion.objects.filter(container=obj, finding_aids_entity__isnull=True, level='A').count()

    def get_digital_versions_in_finding_aids(self, obj):
        """
        Returns the count of digital versions associated with finding-aid entities in the container.
        """
        return DigitalVersion.objects.filter(finding_aids_entity__container=obj).count()

    class Meta:
        model = Container
        fields = ('id', 'reference_code', 'barcode', 'carrier_type', 'total_number', 'total_published_number',
                  'is_removable', 'digital_versions_access_copies', 'digital_versions_masters',
                  'digital_versions_in_finding_aids')
