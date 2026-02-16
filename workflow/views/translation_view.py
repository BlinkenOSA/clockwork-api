import deepl
from django.conf import settings
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from workflow.serializers.translation_serializer import (
    TranslationToEnglishSerializer,
    TranslationToOriginalSerializer,
)


class GetTranslationToOriginal(APIView):
    """
    Translates English text into a specified original language.

    This endpoint uses the DeepL API to translate English source text into
    the language defined by the provided locale.

    Intended for:
        - Workflow automation
        - Metadata localization
        - Assisted cataloging processes

    Authentication:
        Inherited from global API configuration.

    Request Body:
        Uses TranslationToOriginalSerializer.

    Response:
        200 OK:
            {
                "text": "<translated text>"
            }

        400 Bad Request:
            Returned if validation or translation fails.
    """

    swagger_schema = None

    def post(self, request):
        """
        Translates English text into the target locale.

        Args:
            request: HTTP request containing translation payload.

        Returns:
            Response: JSON response containing translated text.
        """
        serializer = TranslationToOriginalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_key = getattr(settings, 'DEEPL_AUTH_KEY', None)
        translator = deepl.Translator(auth_key)

        target_lang = serializer.validated_data['original_locale']

        result = translator.translate_text(
            text=serializer.validated_data['english_text'],
            source_lang='EN',
            target_lang=serializer.validated_data['original_locale'].id
        )

        return Response({'text': result.text}, status=HTTP_200_OK)


class GetTranslationToEnglish(APIView):
    """
    Translates localized text into English.

    This endpoint uses the DeepL API to translate text from a source language
    into standardized English (EN-US).

    Intended for:
        - Metadata normalization
        - Search indexing
        - Editorial review workflows

    Authentication:
        Inherited from global API configuration.

    Request Body:
        Uses TranslationToEnglishSerializer.

    Response:
        200 OK:
            {
                "text": "<translated text>"
            }

        400 Bad Request:
            Returned if validation or translation fails.
    """

    swagger_schema = None

    def post(self, request):
        """
        Translates localized text into English.

        Args:
            request: HTTP request containing translation payload.

        Returns:
            Response: JSON response containing translated text.
        """
        serializer = TranslationToEnglishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_key = getattr(settings, 'DEEPL_AUTH_KEY', None)
        translator = deepl.Translator(auth_key)

        result = translator.translate_text(
            text=serializer.validated_data['original_text'],
            source_lang=serializer.validated_data['original_locale'].id,
            target_lang='EN-US'
        )

        return Response({'text': result.text}, status=HTTP_200_OK)
