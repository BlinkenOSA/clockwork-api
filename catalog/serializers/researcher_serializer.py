from rest_framework import serializers

from catalog.serializer_fields.hcaptcha_field import HCaptchaField
from research.models import Researcher


class ResearcherSerializer(serializers.ModelSerializer):
    captcha = HCaptchaField(read_only=True, required=False)

    class Meta:
        model = Researcher
        fields = '__all__'
