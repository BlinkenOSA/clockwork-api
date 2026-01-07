from rest_framework import serializers
from authority.models import Country, Language, Place, Person, PersonOtherFormat, CorporationOtherFormat, Corporation, \
    Genre, Subject
from drf_writable_nested import WritableNestedModelSerializer


# Country serializers
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin


class CountrySerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full read/write serializer for Country authority records.

    Includes audit fields via UserDataSerializerMixin.
    """

    class Meta:
        model = Country
        fields = '__all__'


class CountrySelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for country selection dropdowns.
    """

    class Meta:
        model = Country
        fields = ('id', 'country')


# Language serializers
class LanguageSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full read/write serializer for Language authority records.
    """

    class Meta:
        model = Language
        fields = '__all__'


class LanguageSelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for language selection components.
    """

    class Meta:
        model = Language
        fields = ('id', 'language')


# Place serializers
class PlaceSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full read/write serializer for Place authority records.
    """

    class Meta:
        model = Place
        fields = '__all__'


class PlaceSelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for place selection dropdowns.
    """

    class Meta:
        model = Place
        fields = ('id', 'place')


# Person serializers
class PersonOtherFormatSerializer(serializers.ModelSerializer):
    """
    Serializer for alternative name formats of a Person.

    The parent Person relationship is excluded because this serializer
    is intended to be used as a nested component.
    """

    class Meta:
        model = PersonOtherFormat
        exclude = ('person',)


class PersonSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Full read/write serializer for Person authority records.

    Features:
        - Nested write support for alternative name formats
        - Computed display name using the model's __str__ method
    """
    name = serializers.CharField(source='__str__', read_only=True)
    person_other_formats = PersonOtherFormatSerializer(many=True, required=False, source='personotherformat_set')

    class Meta:
        model = Person
        fields = '__all__'


class PersonListSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Serializer optimized for listing Person records.

    Includes:
        - Computed display name
        - Finding aids usage counts
        - Removability flag derived from usage
    """

    name = serializers.CharField(source='__str__', read_only=True)
    fa_subject_count = serializers.IntegerField(read_only=True)
    fa_associated_count = serializers.IntegerField(read_only=True)
    fa_total_count = serializers.IntegerField(read_only=True)
    is_removable = serializers.SerializerMethodField()

    def get_is_removable(self, obj: Person) -> bool:
        """
        Determines whether the person can be safely deleted.

        A person is removable if it is not referenced by any finding aids record.
        """
        return obj.fa_total_count == 0

    class Meta:
        model = Person
        fields = ('id', 'name', 'wikidata_id', 'authority_url', 'is_removable', 'fa_subject_count',
                  'fa_associated_count', 'fa_total_count')


class PersonSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for selecting a Person in UI components.
    """

    name = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ('id', 'name')


class SimilarPersonSerializer(serializers.ModelSerializer):
    """
    Serializer used for similarity search results.

    Includes:
        - Computed similarity percentage
        - Key authority reference fields
    """

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
    """
    Serializer for alternative name formats of a Corporation.

    Used as a nested serializer in CorporationSerializer.
    """

    class Meta:
        model = CorporationOtherFormat
        exclude = ('corporation',)


class CorporationSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Full read/write serializer for Corporation authority records.

    Supports nested write operations for alternative name formats.
    """

    corporation_other_formats = CorporationOtherFormatSerializer(many=True, required=False, source='corporationotherformat_set')

    class Meta:
        model = Corporation
        fields = '__all__'


class CorporationSelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for selecting corporations.
    """

    class Meta:
        model = Corporation
        fields = ('id', 'name')


# Genre serializers
class GenreSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full read/write serializer for Genre authority records.
    """

    class Meta:
        model = Genre
        fields = '__all__'


class GenreSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for genre selection.
    """

    class Meta:
        model = Genre
        fields = ('id', 'genre')


# Subject serializers
class SubjectSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Full read/write serializer for Subject authority records.
    """

    class Meta:
        model = Subject
        fields = '__all__'


class SubjectSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for subject selection.
    """

    class Meta:
        model = Subject
        fields = ('id', 'subject')
