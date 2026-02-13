from rest_framework import serializers

from authority.models import Country
from controlled_list.models import Nationality
from research.models import Researcher


class ResearcherListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing researchers in administrative views.

    Provides a compact representation of :class:`research.models.Researcher`
    records, including formatted card numbers, creation timestamps, and
    human-readable country and nationality values.
    """

    name = serializers.CharField()
    card_number = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    country = serializers.SlugRelatedField(slug_field='country', queryset=Country.objects.all())
    # citizenship = serializers.SlugRelatedField(slug_field='nationality', queryset=Nationality.objects.all())

    def get_card_number(self, obj):
        """
        Returns the card number padded to six digits.
        """
        return "%06d" % obj.card_number

    def get_date_created(self, obj):
        """
        Returns the creation timestamp formatted for display.
        """
        return obj.date_created.strftime("%Y-%m-%d %H:%M")

    class Meta:
        model = Researcher
        fields = (
            'id',
            'name',
            'email',
            'card_number',
            'country',
            'date_created',
            'active',
            'approved',
            'is_removable',
        )


class ResearcherReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for detailed researcher views.

    Exposes all model fields and formats the card number for presentation.
    """

    card_number = serializers.SerializerMethodField()

    def get_card_number(self, obj):
        """
        Returns the card number padded to six digits.
        """
        return "%06d" % obj.card_number

    class Meta:
        model = Researcher
        fields = '__all__'


class ResearcherWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating and updating researcher records.

    Allows full read/write access to all fields on the
    :class:`research.models.Researcher` model.
    """

    class Meta:
        model = Researcher
        fields = '__all__'


class ResearcherSelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for researcher selection lists.

    Intended for dropdowns and autocomplete components, exposing only
    the primary key and display name.
    """

    class Meta:
        model = Researcher
        fields = ('id', 'name')
