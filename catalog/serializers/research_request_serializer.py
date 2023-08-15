from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from research.models import Researcher


class RequestItemSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    ams_id = serializers.CharField(required=False)
    origin = serializers.CharField(required=False)
    title = serializers.CharField(required=True)
    call_number = serializers.CharField(required=False)
    digital_version = serializers.CharField(required=False)


class ResearchRequestSerializer(serializers.Serializer):
    card_number = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    request_date = serializers.DateTimeField(required=True)
    items = RequestItemSerializer(many=True)

    def validate_card_number(self, value):
        try:
            Researcher.objects.get(card_number=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The card number you entered is not existing in our system. Please register first!"
            )

    def validate_email(self, value):
        try:
            Researcher.objects.get(email=value)
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
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "The combination of the email and card number is not existing in our system. Are you sure, you've used "
                "the correct data?"
            )

    def to_internal_value(self, data):
        super().to_internal_value(data)

        email = data.get('email', '')
        card_number = data.get('card_number', '')

        if email != "":
            data['researcher'] = Researcher.objects.get(
                email=email,
            )

        if card_number != "":
            data['researcher'] = Researcher.objects.get(
                card_number=card_number,
            )

        return data
