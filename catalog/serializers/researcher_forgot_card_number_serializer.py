from rest_framework import serializers

from catalog.serializer_fields.hcaptcha_field import HCaptchaField


class ResearcherForgotCardNumberSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    email_confirm = serializers.EmailField(required=True)
    # captcha = HCaptchaField(required=True)

    def validate(self, data):
        """
        Check that email is the same as email_again.
        """
        if data['email'] > data['email_confirm']:
            raise serializers.ValidationError("Email and Email Confirmation doesn't match")
        return data