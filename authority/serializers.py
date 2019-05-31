from rest_framework import serializers
from authority.models import Country, Language


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class CountrySelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'country')


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class LanguageSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'language')