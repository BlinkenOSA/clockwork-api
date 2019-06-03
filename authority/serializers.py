from rest_framework import serializers
from authority.models import Country, Language, Place, Person, PersonOtherFormat, CorporationOtherFormat, Corporation, \
    Genre, Subject
from drf_writable_nested import WritableNestedModelSerializer


# Country serializers
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class CountrySelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'country')


# Language serializers
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class LanguageSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'language')


# Place serializers
class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'


class PlaceSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ('id', 'place')


# Person serializers
class PersonOtherFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonOtherFormat
        fields = '__all__'


class PersonSerializer(WritableNestedModelSerializer):
    person_other_formats = PersonOtherFormatSerializer(many=True, source='personotherformat_set')

    class Meta:
        model = Person
        fields = '__all__'


class PersonSelectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ('id', 'name')


# Corporation serializers
class CorporationOtherFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporationOtherFormat
        fields = '__all__'


class CorporationSerializer(WritableNestedModelSerializer):
    corporation_other_formats = PersonOtherFormatSerializer(many=True, source='corporationotherformat_set')

    class Meta:
        model = Corporation
        fields = '__all__'


class CorporationSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Corporation
        fields = ('id', '__str__')


# Genre serializers
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class GenreSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'genre')


# Subject serializers
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class SubjectSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'subject')
