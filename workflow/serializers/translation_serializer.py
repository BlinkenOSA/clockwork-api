from rest_framework import serializers
from controlled_list.models import Locale


class TranslationToOriginalSerializer(serializers.Serializer):
    """
    Serializer for translating English text into an original language.

    Used by workflow translation endpoints to submit English source text
    together with the target locale for automatic or assisted translation.

    Fields:
        - english_text: Source text in English.
        - original_locale: Target language/locale for translation.
    """

    english_text = serializers.CharField(
        label="English Text",
        help_text="Source text in English to be translated."
    )

    original_locale = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Locale.objects.all(),
        label="Original Locale",
        help_text="Target locale for the translated output."
    )


class TranslationToEnglishSerializer(serializers.Serializer):
    """
    Serializer for translating localized text into English.

    Used by workflow translation endpoints to submit text in a local language
    together with its locale for translation into English.

    Fields:
        - original_text: Source text in the original language.
        - original_locale: Locale of the source text.
    """

    original_text = serializers.CharField(
        label="Original Text",
        help_text="Source text in the original language."
    )

    original_locale = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Locale.objects.all(),
        label="Original Locale",
        help_text="Locale of the source language."
    )
