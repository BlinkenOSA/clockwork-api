from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from catalog.serializer_fields.hcaptcha_field import HCaptchaField
from catalog.serializer_fields.origin_field import OriginField
from finding_aids.models import FindingAidsEntity
from research.models import Researcher


class RequestItemSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    ams_id = serializers.CharField(required=False, allow_blank=True)
    origin = OriginField(required=False, allow_blank=True)
    title = serializers.CharField(required=True)
    container = serializers.IntegerField(required=False, allow_null=True)
    call_number = serializers.CharField(required=False, allow_blank=True)
    digital_version = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
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

    def to_internal_value(self, values):
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
    researcher = serializers.IntegerField(required=False, allow_null=True)
    card_number = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    request_date = serializers.DateField(required=True)
    items = RequestItemSerializer(many=True)
    captcha = HCaptchaField(read_only=True, required=False)

    def validate_card_number(self, value):
        try:
            Researcher.objects.get(card_number=value)
            return value
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The card number you entered is not existing in our system. Please register first!"
            )

    def validate_email(self, value):
        try:
            Researcher.objects.get(email=value)
            return value
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The email address you entered is not existing in our system. Please register first!"
            )

    def validate(self, data):
        email = data.get('email', '')
        card_number = data.get('card_number', '0')
        try:
            Researcher.objects.get(
                email=email,
                card_number=card_number
            )
            return data
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The combination of the email and card number is not existing in our system. Are you sure, you've used "
                "the correct data?"
            )

    def to_internal_value(self, values):
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
