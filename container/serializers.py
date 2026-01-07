import json
import datetime
from rest_framework import serializers

from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from container.models import Container
from controlled_list.models import CarrierType
from finding_aids.models import FindingAidsEntity


class ContainerReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for containers.

    This serializer exposes all container fields for retrieval and internal
    read operations where full model state is needed.
    """

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

    class Meta:
        model = Container
        fields = ('id', 'reference_code', 'barcode', 'carrier_type', 'total_number', 'total_published_number',
                  'is_removable')


class ContainerSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for containers.

    Designed for UI selection widgets and lightweight references, including:
        - a reference code formatted for selection contexts
        - a derived digital version duration parsed from technical metadata

    Duration is only returned when video stream metadata is available.
    """

    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    reference_code = serializers.SerializerMethodField(source='container_no')
    digital_version_duration = serializers.SerializerMethodField(source='digital_version_technical_metadata')

    def get_reference_code(self, obj):
        """
        Builds the container reference code used in selection contexts.

        Format:
            <archival_unit.reference_code>:<container_no>
        """
        return "%s:%s" % (obj.archival_unit.reference_code, obj.container_no)

    def get_digital_version_duration(self, obj):
        """
        Extracts a HH:MM:SS duration from the container's technical metadata.

        The duration is derived by:
            1. Parsing digital_version_technical_metadata as JSON
            2. Finding the first stream with codec_type == 'video'
            3. Converting the stream duration (seconds) to HH:MM:SS

        Returns None when:
            - no technical metadata is present
            - no video stream duration is available
            - the metadata cannot be interpreted as expected
        """
        if obj.digital_version_technical_metadata:
            tech_md = json.loads(obj.digital_version_technical_metadata)
            for stream in tech_md['streams']:
                if stream.get('codec_type') == 'video':
                    seconds = float(stream.get('duration'))
                    total_seconds = datetime.timedelta(seconds=seconds).total_seconds()
                    hours, remainder = divmod(total_seconds, 60 * 60)
                    minutes, seconds = divmod(remainder, 60)
                    return "%02d:%02d:%02d" % (hours, minutes, seconds)

    class Meta:
        model = Container
        fields = ('id', 'reference_code', 'digital_version_creation_date',
                  'digital_version_duration', 'barcode', 'carrier_type')
