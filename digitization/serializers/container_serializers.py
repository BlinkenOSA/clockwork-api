import json
import datetime
from rest_framework import serializers
from container.models import Container
from controlled_list.models import CarrierType
from digitization.models import DigitalVersion


class DigitizationContainerLogSerializer(serializers.ModelSerializer):
    """
    Serializer for container digitization log entries.

    Used by digitization-facing dashboards and activity feeds to surface:
        - container identification (reference code, barcode)
        - digital version availability flags and paths
        - derived technical information (duration)
        - carrier type display value
    """

    archival_unit_id = serializers.SerializerMethodField()
    container_no = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    carrier_type = serializers.SerializerMethodField()
    barcode = serializers.SerializerMethodField()

    def get_archival_unit_id(self, obj):
        """
        Returns the ID of the archival unit associated with the container, if available.
        """
        return obj.container.archival_unit.id if obj.container and obj.container.archival_unit else None

    def get_container_no(self, obj):
        """
        Builds a human-readable container reference code.

        Format:
            <archival_unit.reference_code>:<container_no>
        """
        return "%s:%s" % (obj.container.archival_unit.reference_code, obj.container.container_no)

    def get_duration(self, obj):
        """
        Extracts a HH:MM:SS duration from container technical metadata.

        The duration is derived by:
            1. Parsing digital_version_technical_metadata as JSON
            2. Finding the first stream with codec_type == 'video'
            3. Converting the stream duration (seconds) to HH:MM:SS

        Returns None when:
            - no technical metadata is present
            - no video stream duration is available
            - the metadata cannot be interpreted as expected
        """
        tech_md = obj.technical_metadata
        if isinstance(tech_md, str):
            tech_md = json.loads(tech_md)
            for stream in tech_md['streams']:
                if (stream.get('codec_type') == 'video' and stream.get('duration')) or \
                   (stream.get('codec_type') == 'audio' and stream.get('duration')):
                    seconds = float(stream.get('duration'))
                    total_seconds = datetime.timedelta(seconds=seconds).total_seconds()
                    hours, remainder = divmod(total_seconds, 60 * 60)
                    minutes, seconds = divmod(remainder, 60)
                    return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def get_barcode(self, obj):
        """
        Returns the container barcode if available, otherwise returns None.
        """
        return obj.container.barcode if obj.container and obj.container.barcode else None

    def get_carrier_type(self, obj):
        """
        Returns the carrier type slug if available, otherwise returns None.
        """
        return obj.container.carrier_type.type if obj.container and obj.container.carrier_type else None

    class Meta:
        model = DigitalVersion
        fields = ('id', 'barcode', 'archival_unit_id', 'container_no', 'duration', 'carrier_type',
                  'available_online', 'available_research_cloud', 'research_cloud_path', 'creation_date',
                  'technical_metadata', 'level')


class DigitizationContainerDataSerializer(serializers.ModelSerializer):
    """
    Serializer exposing parsed technical metadata for a container.

    This serializer is intended for clients that need the structured
    technical metadata object rather than the raw JSON string stored on
    the model.
    """

    technical_metadata = serializers.SerializerMethodField()

    def get_technical_metadata(self, obj):
        """
        Returns the technical metadata as a parsed JSON object.

        Returns False when no technical metadata is available.
        """
        return json.loads(obj.technical_metadata) if obj.technical_metadata else False

    class Meta:
        model = DigitalVersion
        fields = ('technical_metadata',)