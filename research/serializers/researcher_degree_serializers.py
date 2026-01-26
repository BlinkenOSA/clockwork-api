from rest_framework import serializers
from research.models import ResearcherDegree


class ResearcherDegreeReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for researcher degree records.

    Exposes all fields of :class:`research.models.ResearcherDegree` and is
    typically used in detail or list endpoints where full degree metadata
    is required.
    """

    class Meta:
        model = ResearcherDegree
        fields = '__all__'


class ResearcherDegreeWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for researcher degree records.

    Supports creation and update of :class:`research.models.ResearcherDegree`
    entries. All model fields are writable.
    """

    class Meta:
        model = ResearcherDegree
        fields = '__all__'


class ResearcherDegreeSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for researcher degree selection.

    Intended for dropdowns and selection lists, exposing only the primary
    identifier and degree label.
    """

    class Meta:
        model = ResearcherDegree
        fields = ('id', 'degree')
