"""
Serializers for archival research request submission.

These serializers validate:
    - researcher identity
    - request items
    - item origins
    - captcha verification

They also normalize input data to resolve foreign keys
before request processing.
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from catalog.serializer_fields.hcaptcha_field import HCaptchaField
from catalog.serializer_fields.origin_field import OriginField
from finding_aids.models import FindingAidsEntity
from research.models import Researcher


class RequestItemSerializer(serializers.Serializer):
    """
    Validates a single requested item.

    Items may originate from:
        - Finding Aids (origin == 'FA')
        - Library/Film Library sources

    For FA items, container resolution is automatic.
    """

    id = serializers.CharField(required=True)
    ams_id = serializers.CharField(required=False, allow_blank=True)
    origin = OriginField(required=False, allow_blank=True)
    title = serializers.CharField(required=True)
    container = serializers.IntegerField(required=False, allow_null=True)
    call_number = serializers.CharField(required=False, allow_blank=True)
    volume = serializers.CharField(required=False, allow_blank=True)
    digital_version = serializers.CharField(required=False, allow_blank=True)
    restricted = serializers.BooleanField(required=False, allow_null=True, default=False)

    def validate(self, data: dict) -> dict:
        """
        Ensures finding aids items reference a valid AMS entity.
        """
        origin = data.get('origin', None)
        ams_id = data.get('ams_id', None)

        if origin == 'FA':
            if not ams_id:
                raise serializers.ValidationError({"ams_id": "AMS ID field is required!"})

            try:
                FindingAidsEntity.objects.get(id=ams_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError({"ams_id": "AMS ID field invalid!"})

        return data

    def to_internal_value(self, values: dict) -> dict:
        """
        Resolves container IDs for finding aids items automatically.
        """
        data = super().to_internal_value(values)

        origin = data.get('origin', None)
        ams_id = data.get('ams_id', None)

        if origin == 'FA':
            finding_aids_entity = FindingAidsEntity.objects.get(id=ams_id)
            data['container'] = finding_aids_entity.container.id
        else:
            data['container'] = None

        return data


class ResearchRequestSerializer(serializers.Serializer):
    """
    Validates a complete research request submission.

    This serializer:
        - validates researcher identity via email + card number
        - validates all request items
        - enforces captcha verification
        - resolves researcher ID for downstream processing
    """

    researcher = serializers.IntegerField(required=False, allow_null=True)
    card_number = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    request_date = serializers.DateField(required=True)
    items = RequestItemSerializer(many=True)
    captcha = HCaptchaField(required=True)
    research_subject = serializers.CharField(required=False, allow_blank=True)
    motivation = serializers.CharField(required=False, allow_blank=True)

    def validate_card_number(self, value: str) -> str:
        """
        Validates if card number resolves to an existing researcher.
        """
        try:
            Researcher.objects.get(card_number=value)
            return value
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The card number you entered is not existing in our system. Please register first!"
            )

    def validate_email(self, value: str) -> str:
        """
        Validates if email resolves to an existing researcher.
        """
        try:
            Researcher.objects.get(email=value)
            return value
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The email address you entered is not existing in our system. Please register first!"
            )

    def validate(self, data: dict) -> dict:
        """
        Validates if the combination of email and card number resolves to an existing researcher.
        """
        email = data.get('email', '')
        card_number = data.get('card_number', '0')
        try:
            researcher = Researcher.objects.get(
                email=email,
                card_number=card_number
            )
        except Researcher.DoesNotExist:
            raise serializers.ValidationError(
                "No account found with this email and card number."
            )

        # Now we know the user exists
        if not researcher.approved:
            raise serializers.ValidationError(
                "Your account has not been approved yet."
            )

        if not researcher.active:
            raise serializers.ValidationError(
                "Your account is inactive. Please contact support at archivum@ceu.edu."
            )

        return data

    def to_internal_value(self, values: dict) -> dict:
        """
        Resolves the Researcher ID from email and/or card number.
        """
        data = super().to_internal_value(values)

        email = data.get('email', '')
        card_number = data.get('card_number', '')

        if email != "":
            data['researcher'] = Researcher.objects.get(
                email=email,
            ).id

        if card_number != "":
            data['researcher'] = Researcher.objects.get(
                card_number=card_number,
            ).id

        return data
