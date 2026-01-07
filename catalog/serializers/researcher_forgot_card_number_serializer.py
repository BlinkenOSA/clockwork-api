"""
Serializer for researcher card number recovery requests.

This serializer validates the minimal data required to initiate
a card number recovery workflow:

    - primary email address
    - confirmation of the email address
    - hCaptcha verification token

No database interaction occurs in this serializer.
"""

from rest_framework import serializers

from catalog.serializer_fields.hcaptcha_field import HCaptchaField


class ResearcherForgotCardNumberSerializer(serializers.Serializer):
    """
    Validates input for researcher card number recovery.

    This serializer ensures:
        - a valid email address is provided
        - the confirmation email matches
        - hCaptcha verification succeeds

    The captcha field is validation-only and never persisted.
    """

    email = serializers.EmailField(required=True)
    email_confirm = serializers.EmailField(required=True)
    captcha = HCaptchaField(required=True)

    def validate(self, data):
        """
        Ensures that the email and confirmation email match.

        Args:
            data:
                Dictionary containing validated field values.

        Returns:
            Validated data if emails match.

        Raises:
            ValidationError if the email addresses differ.
        """
        if data['email'] != data['email_confirm']:
            raise serializers.ValidationError("Email and Email Confirmation doesn't match")
        return data
