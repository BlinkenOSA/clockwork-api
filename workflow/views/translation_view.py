import deepl
from django.conf import settings
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from workflow.serializers.translation_serializer import TranslationToEnglishSerializer, TranslationToOriginalSerializer


class GetTranslationToOriginal(APIView):
    def post(self, request):
        serializer = TranslationToOriginalSerializer(data=request.data)
        serializer.is_valid()

        auth_key = getattr(settings, 'DEEPL_AUTH_KEY', None)
        translator = deepl.Translator(auth_key)

        result = translator.translate_text(
            text=serializer.data['english_text'],
            source_lang='EN',
            target_lang=serializer.data['original_locale']
        )
        return Response({'text': result.text}, status=HTTP_200_OK)


class GetTranslationToEnglish(APIView):
    def post(self, request):
        serializer = TranslationToEnglishSerializer(data=request.data)
        serializer.is_valid()

        auth_key = getattr(settings, 'DEEPL_AUTH_KEY', None)
        translator = deepl.Translator(auth_key)

        result = translator.translate_text(
            text=serializer.data['original_text'],
            source_lang=serializer.data['original_locale'],
            target_lang='EN-US'
        )
        return Response({'text': result.text}, status=HTTP_200_OK)
