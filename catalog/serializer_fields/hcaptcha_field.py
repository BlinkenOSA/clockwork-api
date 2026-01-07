"""
Custom serializer field for hCaptcha validation.

This field validates a client-side hCaptcha response token by
performing a server-to-server verification request to hCaptcha.

The field:
    - accepts a single token string
    - validates it against hCaptcha servers
    - never stores the value
"""
import requests
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class HCaptchaField(serializers.Field):
    """
    Validates hCaptcha challenge responses.

    This field performs a blocking HTTP request to the configured
    hCaptcha verification endpoint.

    The value is discarded after validation and never serialized
    or persisted.
    """

    def to_internal_value(self, data: str) -> str:
        """
        Validates the provided hCaptcha response token.

        Args:
            data:
                hCaptcha response token provided by the client.

        Returns:
            Empty string (value is not stored).

        Raises:
            ValidationError if:
                - token is missing
                - hCaptcha verification fails
                - verification service is unreachable
        """
        captcha_url = getattr(settings, 'HCAPTCHA_VERIFY_URL', None)
        sitekey = getattr(settings, 'HCAPTCHA_SITE_KEY', None)

        # Check the submitted captcha
        if data:
            data = {
                'secret': sitekey,
                'response': data
            }
            r = requests.post(captcha_url, data=data)

            if r.status_code == 200:
                response = r.json()
                if not response['success']:
                    raise ValidationError('Captcha is invalid, please refresh the page!')
                else:
                    return ''
            else:
                raise ValidationError('Error communicating with HCaptcha server!')
        else:
            raise ValidationError('Captcha is required!')

    def to_representation(self, value) -> str:
        """
        Prevents the captcha value from ever being exposed.

        Returns:
            Empty string.
        """
        return ''
