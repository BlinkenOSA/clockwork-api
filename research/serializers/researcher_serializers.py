from rest_framework import serializers
from research.models import Researcher


class ResearcherReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    card_number = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()

    def get_card_number(self, obj):
        return "%06d" % obj.card_number

    def get_date_created(self, obj):
        return obj.date_created.strftime("%Y-%m-%d %H:%M")

    def get_country(self, obj):
        return obj.country.country if obj.country else None

    class Meta:
        model = Researcher
        fields = '__all__'


class ResearcherWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Researcher
        fields = '__all__'


class ResearcherSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Researcher
        fields = ('id', 'last_name', 'first_name')

