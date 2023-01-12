from rest_framework import serializers

from authority.models import Country
from controlled_list.models import Nationality
from research.models import Researcher


class ResearcherReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    card_number = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    country = serializers.SlugRelatedField(slug_field='country', queryset=Country.objects.all())
    citizenship = serializers.SlugRelatedField(slug_field='nationality', queryset=Nationality.objects.all())

    def get_card_number(self, obj):
        return "%06d" % obj.card_number

    def get_date_created(self, obj):
        return obj.date_created.strftime("%Y-%m-%d %H:%M")

    class Meta:
        model = Researcher
        fields = ('id', 'name', 'email', 'card_number', 'country', 'citizenship', 'date_created',
                  'active', 'approved', 'is_removable')


class ResearcherWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Researcher
        fields = '__all__'


class ResearcherSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Researcher
        fields = ('id', 'last_name', 'first_name')

