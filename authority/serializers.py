from rest_framework import serializers
from authority.models import Country, Language, Place, Person, PersonOtherFormat, CorporationOtherFormat, Corporation, \
    Genre, Subject
from drf_writable_nested import WritableNestedModelSerializer


# Country serializers
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin


class CountrySerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class CountrySelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'country')


# Language serializers
class LanguageSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class LanguageSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'language')


# Place serializers
class PlaceSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
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
        exclude = ('person',)


class PersonSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    name = serializers.CharField(source='__str__', read_only=True)
    person_other_formats = PersonOtherFormatSerializer(many=True, required=False, source='personotherformat_set')
    fa_subject_count = serializers.IntegerField(read_only=True)
    fa_associated_count = serializers.IntegerField(read_only=True)
    fa_total_count = serializers.IntegerField(read_only=True)
    is_removable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Person
        fields = '__all__'


class PersonListSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    name = serializers.CharField(source='__str__', read_only=True)
    fa_subject_count = serializers.IntegerField(read_only=True)
    fa_associated_count = serializers.IntegerField(read_only=True)
    fa_total_count = serializers.IntegerField(read_only=True)
    is_removable = serializers.SerializerMethodField()

    def get_is_removable(self, obj):
        return obj.fa_total_count == 0

    class Meta:
        model = Person
        fields = ('id', 'name', 'wikidata_id', 'authority_url', 'is_removable', 'fa_subject_count',
                  'fa_associated_count', 'fa_total_count')


class PersonSelectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ('id', 'name')


class SimilarPersonSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='__str__')
    similarity_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Person
        fields = [
            'id', 'name', 'wikidata_id', 'wiki_url', 'authority_url', 'other_url',
            'similarity_percent'
        ]


# Corporation serializers
class CorporationOtherFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporationOtherFormat
        exclude = ('corporation',)


class CorporationSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    corporation_other_formats = CorporationOtherFormatSerializer(many=True, required=False, source='corporationotherformat_set')

    class Meta:
        model = Corporation
        fields = '__all__'


class CorporationSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Corporation
        fields = ('id', 'name')


# Genre serializers
class GenreSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class GenreSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'genre')


# Subject serializers
class SubjectSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class SubjectSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'subject')
