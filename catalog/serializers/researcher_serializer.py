"""
Serializer for public researcher registration.

This serializer wraps the Researcher model and adds mandatory
hCaptcha validation via a custom serializer field.

The captcha value itself is never persisted.
"""
from rest_framework import serializers

from catalog.serializer_fields.hcaptcha_field import HCaptchaField
from research.models import Researcher


class ResearcherSerializer(serializers.ModelSerializer):
    """
    Serializes Researcher registration data.

    Includes a write-only hCaptcha field used exclusively for
    spam and abuse prevention during public registration.
    """
    captcha = HCaptchaField(required=True)

    class Meta:
        model = Researcher
        fields = ['last_name', 'first_name', 'middle_name', 'email', 'country', 'city_abroad', 'address_abroad',
                  'address_house_number', 'occupation', 'department', 'degree', 'employer_or_school',
                  'research_subject', 'captcha']
