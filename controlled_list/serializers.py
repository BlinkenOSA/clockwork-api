from rest_framework import serializers

from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.models import (
    AccessRight,
    ArchivalUnitTheme,
    Building,
    CarrierType,
    CorporationRole,
    DateType,
    ExtentUnit,
    GeoRole,
    Keyword,
    LanguageUsage,
    Locale,
    PersonRole,
    PrimaryType,
    ReproductionRight,
    RightsRestrictionReason,
    Nationality,
    IdentifierType,
)


"""
Serializers for controlled vocabulary entries.

This module provides two serializer variants per controlled list model:
    - <Model>Serializer: full representation used for CRUD and administration
      views, typically including `is_removable`.
    - <Model>SelectSerializer: minimal representation used for selection
      widgets (e.g., dropdowns, autocomplete).
"""


# AccessRight serializers
class AccessRightSerializer(serializers.ModelSerializer):
    """
    Full serializer for AccessRight entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = AccessRight
        fields = ('id', 'statement', 'is_removable')


class AccessRightSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for AccessRight entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = AccessRight
        fields = ('id', 'statement')


# ArchivalUnitTheme serializers
class ArchivalUnitThemeSerializer(serializers.ModelSerializer):
    """
    Full serializer for ArchivalUnitTheme entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = ArchivalUnitTheme
        fields = ('id', 'theme', 'is_removable')


class ArchivalUnitThemeSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for ArchivalUnitTheme entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = ArchivalUnitTheme
        fields = ('id', 'theme')


# Building serializers
class BuildingSerializer(serializers.ModelSerializer):
    """
    Full serializer for Building entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = Building
        fields = ('id', 'building', 'is_removable')


class BuildingSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for Building entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = Building
        fields = ('id', 'building')


# CarrierType serializers
class CarrierTypeSerializer(serializers.ModelSerializer):
    """
    Full serializer for CarrierType entries.

    Exposes dimensional and labeling metadata used for storage and
    container formatting.
    """

    class Meta:
        model = CarrierType
        fields = (
            'id',
            'type',
            'type_original_language',
            'width',
            'height',
            'depth',
            'jasper_file',
            'is_removable',
        )


class CarrierTypeSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for CarrierType entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = CarrierType
        fields = ('id', 'type')


# CorporationRole serializers
class CorporationRoleSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full serializer for CorporationRole entries.

    Applies user metadata behavior via UserDataSerializerMixin and includes
    `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = CorporationRole
        fields = ('id', 'role', 'is_removable')


class CorporationRoleSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for CorporationRole entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = CorporationRole
        fields = ('id', 'role')


# DateType serializers
class DateTypeSerializer(serializers.ModelSerializer):
    """
    Full serializer for DateType entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = DateType
        fields = ('id', 'type', 'is_removable')


class DateTypeSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for DateType entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = DateType
        fields = ('id', 'type')


# ExtentUnit serializers
class ExtentUnitSerializer(serializers.ModelSerializer):
    """
    Full serializer for ExtentUnit entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = ExtentUnit
        fields = ('id', 'unit', 'is_removable')


class ExtentUnitSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for ExtentUnit entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = ExtentUnit
        fields = ('id', 'unit')


# GeoRole serializers
class GeoRoleSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full serializer for GeoRole entries.

    Applies user metadata behavior via UserDataSerializerMixin and includes
    `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = GeoRole
        fields = ('id', 'role', 'is_removable')


class GeoRoleSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for GeoRole entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = GeoRole
        fields = ('id', 'role')


# IdentifierType serializers
class IdentifierTypeSerializer(serializers.ModelSerializer):
    """
    Full serializer for IdentifierType entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = IdentifierType
        fields = ('id', 'type', 'is_removable')


class IdentifierTypeSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for IdentifierType entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = IdentifierType
        fields = ('id', 'type')


# Keyword serializers
class KeywordSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full serializer for Keyword entries.

    Applies user metadata behavior via UserDataSerializerMixin and includes
    `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = Keyword
        fields = ('id', 'keyword', 'is_removable')


class KeywordSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for Keyword entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = Keyword
        fields = ('id', 'keyword')


# LanguageUsage serializers
class LanguageUsageSerializer(serializers.ModelSerializer):
    """
    Full serializer for LanguageUsage entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = LanguageUsage
        fields = ('id', 'usage', 'is_removable')


class LanguageUsageSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for LanguageUsage entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = LanguageUsage
        fields = ('id', 'usage')


# Locale serializers
class LocaleSerializer(serializers.ModelSerializer):
    """
    Full serializer for Locale entries.

    Uses a short string primary key and includes `is_removable` to support
    safe deletion workflows.
    """

    class Meta:
        model = Locale
        fields = ('id', 'locale_name', 'is_removable')


class LocaleSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for Locale entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = Locale
        fields = ('id', 'locale_name')


# Nationality serializers
class NationalitySerializer(serializers.ModelSerializer):
    """
    Full serializer for Nationality entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = Nationality
        fields = ('id', 'nationality', 'is_removable')


class NationalitySelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for Nationality entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = Nationality
        fields = ('id', 'nationality')


# PersonRole serializers
class PersonRoleSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full serializer for PersonRole entries.

    Applies user metadata behavior via UserDataSerializerMixin and includes
    `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = PersonRole
        fields = ('id', 'role', 'is_removable')


class PersonRoleSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for PersonRole entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = PersonRole
        fields = ('id', 'role')


# PrimaryType serializers
class PrimaryTypeSerializer(serializers.ModelSerializer):
    """
    Full serializer for PrimaryType entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = PrimaryType
        fields = ('id', 'type', 'is_removable')


class PrimaryTypeSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for PrimaryType entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = PrimaryType
        fields = ('id', 'type')


# ReproductionRight serializers
class ReproductionRightSerializer(serializers.ModelSerializer):
    """
    Full serializer for ReproductionRight entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = ReproductionRight
        fields = ('id', 'statement', 'is_removable')


class ReproductionRightSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for ReproductionRight entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = ReproductionRight
        fields = ('id', 'statement')


# RightsRestrictionReason serializers
class RightsRestrictionReasonSerializer(serializers.ModelSerializer):
    """
    Full serializer for RightsRestrictionReason entries.

    Includes `is_removable` to support safe deletion workflows.
    """

    class Meta:
        model = RightsRestrictionReason
        fields = ('id', 'reason', 'is_removable')


class RightsRestrictionReasonSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for RightsRestrictionReason entries.

    Used for lightweight lookups and selection widgets.
    """

    class Meta:
        model = RightsRestrictionReason
        fields = ('id', 'reason')
