from rest_framework import serializers

from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.models import AccessRight, ArchivalUnitTheme, Building, CarrierType, CorporationRole, DateType, \
    ExtentUnit, GeoRole, Keyword, LanguageUsage, Locale, PersonRole, PrimaryType, ReproductionRight, \
    RightsRestrictionReason


# AccessRight serializers
class AccessRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRight
        fields = '__all__'


class AccessRightSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRight
        fields = ('id', 'statement')


# ArchivalUnitTheme serializers
class ArchivalUnitThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnitTheme
        fields = '__all__'


class ArchivalUnitThemeSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnitTheme
        fields = ('id', 'theme')


# Building serializers
class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'


class BuildingSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ('id', 'building')


# CarrierType serializers
class CarrierTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierType
        fields = '__all__'


class CarrierTypeSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierType
        fields = ('id', 'type')


# CorporationRole serializers
class CorporationRoleSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CorporationRole
        fields = '__all__'


class CorporationRoleSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporationRole
        fields = ('id', 'role')


# DateType serializers
class DateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateType
        fields = '__all__'


class DateTypeSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateType
        fields = ('id', 'type')


# ExtentUnit serializers
class ExtentUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtentUnit
        fields = '__all__'


class ExtentUnitSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtentUnit
        fields = ('id', 'unit')


# GeoRole serializers
class GeoRoleSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = GeoRole
        fields = '__all__'


class GeoRoleSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoRole
        fields = ('id', 'role')


# Keyword serializers
class KeywordSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'


class KeywordSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ('id', 'keyword')


# LanguageUsage serializers
class LanguageUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageUsage
        fields = '__all__'


class LanguageUsageSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageUsage
        fields = ('id', 'keyword')


# Locale serializers
class LocaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locale
        fields = '__all__'


class LocaleSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locale
        fields = ('id', 'locale_name')


# PersonRole serializers
class PersonRoleSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = PersonRole
        fields = '__all__'


class PersonRoleSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonRole
        fields = ('id', 'role')


# PrimaryType serializers
class PrimaryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimaryType
        fields = '__all__'


class PrimaryTypeSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimaryType
        fields = ('id', 'type')


# ReproductionRight serializers
class ReproductionRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionRight
        fields = '__all__'


class ReproductionRightSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionRight
        fields = ('id', 'statement')


# RightsRestrictionReason serializers
class RightsRestrictionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RightsRestrictionReason
        fields = '__all__'


class RightsRestrictionReasonSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = RightsRestrictionReason
        fields = ('id', 'reason')