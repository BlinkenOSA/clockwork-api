"""
Custom serializer field for ReCaptcha validation.

This field validates a client-side ReCaptcha response token by
performing a server-to-server verification request to Google ReCaptcha.

The field:
    - accepts a single token string
    - validates it against ReCaptcha servers
    - never stores the value
"""
from requests.exceptions import RequestException
from clockwork_api.http import post
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ReCaptchaField(serializers.Field):
    """
    Validates ReCaptcha challenge responses.

    This field performs a blocking HTTP request to the configured
    ReCaptcha verification endpoint.

    The value is discarded after validation and never serialized
    or persisted.
    """

    def to_internal_value(self, token: str) -> str:
        """
        Validates the provided ReCaptcha response token.

        Args:
            token:
                ReCaptcha response token provided by the client.

        Returns:
            Empty string (value is not stored).

        Raises:
            ValidationError if:
                - token is missing
                - ReCaptcha verification fails
                - verification service is unreachable
        """
        verify_url = getattr(settings, "RECAPTCHA_VERIFY_URL", None)
        secret_key = getattr(settings, "RECAPTCHA_SECRET_KEY", None)

        if not verify_url or not secret_key:
            raise ValidationError("Captcha is misconfigured. Please try again later!")

        if not token:
            raise ValidationError("Captcha is required!")

        payload = {
            "secret": secret_key,
            "response": token,
            # optional: "remoteip": self.context.get("request").META.get("REMOTE_ADDR")
        }

        try:
            r = post(verify_url, data=payload)
        except RequestException:
            raise ValidationError("Error communicating with reCAPTCHA server!")

        if r.status_code != 200:
            raise ValidationError("Error communicating with reCAPTCHA server!")

        body = r.json()
        if not body.get("success"):
            raise ValidationError("Captcha is invalid, please refresh the page!")

        # If using reCAPTCHA v3, also validate score/action:
        # if body.get("score", 0) < settings.RECAPTCHA_MIN_SCORE:
        #     raise ValidationError("Captcha score too low.")
        # if body.get("action") != "expected_action":
        #     raise ValidationError("Captcha action mismatch.")

        return ""


def to_representation(self, value) -> str:
        """
        Prevents the captcha value from ever being exposed.

        Returns:
            Empty string.
        """
        return ''
