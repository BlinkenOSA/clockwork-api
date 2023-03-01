from rest_framework import serializers
from controlled_list.models import Locale


class TranslationToOriginalSerializer(serializers.Serializer):
    english_text = serializers.CharField()
    original_locale = serializers.PrimaryKeyRelatedField(
        required=True, queryset=Locale.objects.all()
    )


class TranslationToEnglishSerializer(serializers.Serializer):
    original_text = serializers.CharField()
    original_locale = serializers.PrimaryKeyRelatedField(
        required=True, queryset=Locale.objects.all()
    )
