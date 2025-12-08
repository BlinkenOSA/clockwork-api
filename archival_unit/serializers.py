from typing import Optional, List, Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity


class ArchivalUnitSeriesSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for series-level archival units.

    Exposes only basic hierarchical identifiers, title, and whether the unit
    is removable (provided by queryset annotation).
    """
    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'reference_code', 'title', 'is_removable')


class ArchivalUnitSubfondsSerializer(serializers.ModelSerializer):
    """
    Serializer for subfonds-level units.

    Includes:
        - Basic hierarchical information
        - Nested series children if present
    """
    children = serializers.SerializerMethodField()

    def get_children(self, obj: ArchivalUnit) -> Optional[List[dict[str, Any]]]:
        """
        Returns serialized series children, or None if no children exist.
        """
        if obj.children.count() > 0:
            return ArchivalUnitSeriesSerializer(obj.children, many=True).data
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'is_removable')


class ArchivalUnitFondsSerializer(serializers.ModelSerializer):
    """
    Serializer for fonds-level units.

    Includes:
        - Basic hierarchical identifiers
        - Nested subfonds children if present
    """
    children = serializers.SerializerMethodField()

    def get_children(self, obj: ArchivalUnit) -> Optional[List[dict[str, Any]]]:
        """
        Returns serialized subfonds children, or None if no children exist.
        """
        if obj.children.count() > 0:
            return ArchivalUnitSubfondsSerializer(obj.children, many=True).data
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'is_removable')


class ArchivalUnitPreCreateSerializer(serializers.ModelSerializer):
    """
    Serializer providing pre-filled metadata for creating a new archival unit
    under an existing one.

    Exposes:
        - Parent ID
        - Fonds/subfonds metadata (title + acronym)
        - Next-level indicator (e.g., F -> SF, SF -> S)
    """
    parent = serializers.IntegerField(source='pk')
    fonds_title = serializers.SerializerMethodField()
    fonds_acronym = serializers.SerializerMethodField()
    subfonds_title = serializers.SerializerMethodField()
    subfonds_acronym = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    # ---- Fonds helpers -----------------------------------------------------

    def get_fonds_title(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the fonds-level title for this archival unit.

        Logic:
            - If the unit is a fonds (F), return its own title.
            - If the unit is a subfonds (SF), return the parent fonds title.
            - If deeper (S), no fonds title is returned here because the
              pre-create endpoint is only used for F → SF or SF → S transitions.

        Args:
            obj: The archival unit instance being serialized.

        Returns:
            The fonds title, or None if not applicable.
        """
        if obj.level == 'F':
            return obj.title
        elif obj.level == 'SF':
            return obj.parent.title

    def get_fonds_acronym(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the fonds-level acronym for this archival unit.

        Logic mirrors `get_fonds_title`:
            - F  → return own acronym
            - SF → return parent fonds acronym

        Args:
            obj: The archival unit instance.

        Returns:
            The fonds acronym, or None if not applicable.
        """
        if obj.level == 'F':
            return obj.acronym
        elif obj.level == 'SF':
            return obj.parent.acronym

    # ---- Subfonds helpers -----------------------------------------------------

    def get_subfonds_title(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the subfonds-level title for this archival unit.

        Logic:
            - If the unit is SF, return its own title.
            - If the unit is S, return the parent subfonds title.
            - Fonds-level units do not have subfonds information.

        Args:
            obj: The archival unit instance.

        Returns:
            The subfonds title or None.
        """
        if obj.level == 'SF':
            return obj.title
        elif obj.level == 'S':
            return obj.parent.title

    def get_subfonds_acronym(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the subfonds-level acronym for this archival unit.

        Logic mirrors `get_subfonds_title`:
            - SF → own acronym
            - S  → parent acronym

        Args:
            obj: The archival unit instance.

        Returns:
            The subfonds acronym or None.
        """
        if obj.level == 'SF':
            return obj.acronym
        elif obj.level == 'S':
            return obj.parent.acronym

    # ---- Level helper ------------------------------------------------------

    def get_level(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the next child level that can be created under this unit.

        Mapping:
            F  → SF
            SF → S

        Args:
            obj: The parent archival unit.

        Returns:
            The next hierarchical level or None if no further levels exist.
        """
        if obj.level == 'F':
            return 'SF'
        elif obj.level == 'SF':
            return 'S'

    class Meta:
        model = ArchivalUnit
        fields = ('parent',
                  'fonds', 'fonds_title', 'fonds_acronym',
                  'subfonds', 'subfonds_title', 'subfonds_acronym',
                  'series', 'level')


class ArchivalUnitReadSerializer(serializers.ModelSerializer):
    """
    Full read serializer for archival units.

    Adds derived metadata for:
        - Fonds title/acronym
        - Subfonds title/acronym
    """
    fonds_title = serializers.SerializerMethodField()
    fonds_acronym = serializers.SerializerMethodField()
    subfonds_title = serializers.SerializerMethodField()
    subfonds_acronym = serializers.SerializerMethodField()

    # ---- Fonds helpers -----------------------------------------------------

    def get_fonds_title(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the title of the fonds to which this archival unit belongs.

        Logic:
            - F  → None (this unit is itself a fonds)
            - SF → title of the parent fonds
            - S  → title of the grandparent fonds

        Args:
            obj: The archival unit instance.

        Returns:
            The fonds title, or None if the unit is itself a fonds.
        """
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return obj.parent.title
        else:
            return obj.parent.parent.title

    def get_fonds_acronym(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the acronym of the fonds to which this unit belongs.

        Logic:
             - F  → None
             - SF → parent acronym
             - S  → grandparent acronym

        Args:
            obj: The archival unit instance.

        Returns:
            The fonds acronym or None.
        """
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return obj.parent.acronym
        else:
            return obj.parent.parent.acronym

    # ---- Subfonds helpers -----------------------------------------------------

    def get_subfonds_title(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the subfonds title associated with this unit.

        Logic:
            - F  → None (fonds have no subfonds)
            - SF → None (subfonds itself is the subfonds)
            - S  → title of the parent subfonds

        Args:
            obj: The archival unit instance.

        Returns:
            The subfonds title or None.
        """
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return None
        else:
            return obj.parent.title

    def get_subfonds_acronym(self, obj: ArchivalUnit) -> Optional[str]:
        """
        Returns the subfonds acronym associated with this unit.

        Logic:
            - F  → None
            - SF → None
            - S  → parent's acronym

        Args:
            obj: The archival unit instance.

        Returns:
            The subfonds acronym or None.
        """
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return None
        else:
            return obj.parent.acronym

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class ArchivalUnitWriteSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for creating and updating archival units.

    Adds validation for:
        - Status (must be Final or Draft)
        - Level (must be F, SF, or S)

    Reference code fields are writeable due to legacy workflows but normally
    are overridden in ArchivalUnit.save().
    """
    reference_code = serializers.CharField(required=False)
    reference_code_id = serializers.CharField(required=False)

    def validate_status(self, value: str) -> str:
        if value not in ['Final', 'Draft']:
            raise ValidationError("Status should be either: 'Final' or 'Draft'")
        return value

    def validate_level(self, value: str) -> str:
        if value not in ['F', 'SF', 'S']:
            raise ValidationError("Level should be either: 'Fonds', 'Subfonds', 'Series'")
        return value

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class ArchivalUnitSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for archival unit selection lists.

    Adds:
        - container_count: number of container objects under this unit
        - folder_count: number of finding-aid entities under this unit
    """
    container_count = serializers.SerializerMethodField()
    folder_count = serializers.SerializerMethodField()

    def get_container_count(self, obj):
        if obj.level == 'S':
            return Container.objects.filter(archival_unit=obj).count()
        else:
            return None

    def get_folder_count(self, obj):
        if obj.level == 'S':
            return FindingAidsEntity.objects.filter(archival_unit=obj).exclude(is_template=True).count()
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'level', 'reference_code', 'title', 'title_full', 'container_count', 'folder_count')
